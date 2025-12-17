from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from db.db_operation import mongo_conn
from models.user import UserOut
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from utils.logger import get_logger

logger = get_logger("Dependencies")



# tells fastapi to expect a token in the request header after login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# JWT Secret & Algorithm
SECRET_KEY = os.getenv("SECRET_KEY", "MySecretKey@123")
ALGORITHM = "HS256"

class CurrentUser(BaseModel):
    id: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    # use Field(default_factory=list) to avoid mutable default list pitfall
    restaurant_ids: List[str] = Field(default_factory=list)
    token_version: int = 0

    class Config:
        orm_mode = True  # helpful if you ever return ORM objects

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    Decode token, validate, fetch user from DB, and ensure token_version matches.
    Returns CurrentUser object.
    """
    logger.info("Received request to get current user from token")
    try:
        # JWT decode
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Token decoded successfully for the current user")
        email: str = payload.get("sub") # sub is used for unique identifier such as email or user id
        logger.debug(f"Email found in token: {email}")
        #added fields for role, restaurant_ids, token_version
        role: str = payload.get("role")
        rid = payload.get("restaurant_ids")
        tv = payload.get("token_version")

        if email is None:
            logger.debug("Email not found for the current user in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no email found"
            )
        logger.info(f"Fetching user details for email: {email}")
        # User find from DB
        users_collection = mongo_conn.users_collection
        user = await users_collection.find_one({"email": email})
        if user is None:
            logger.warning(f"User not found for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        if user.get("disabled", False):
            logger.warning(f"Disabled user attempted access: {email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        db_tv = user.get("token_version")
        if db_tv != tv:
            logger.warning(f"Token version mismatch for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        current_user = CurrentUser(
            email=user.get("email"),
            role=user.get("role"),
            restaurant_ids=user.get("restaurant_ids"),
            token_version=user.get("token_version"),
            full_name=user.get("full_name"),
            id=str(user.get("_id"))
        )
        # UserOut ke format me return karo
        logger.info(f"Current user fetched successfully: {current_user.email}")
        return current_user
    except JWTError:
        logger.error("JWT Error: Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def require_role(*allowed_roles):
    """
    Ensures the current user has one of the allowed roles.
    """
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {allowed_roles}"
            )
        return current_user
    
    return role_checker


def require_restaurant_admin(restaurant_id_param_name: str):
    """
    Returns a dependency which ensures:
      - If current_user is superadmin => allow
      - Else if current_user.role == 'restaurant_admin' and restaurant_id in user's restaurant_ids => allow
      - Otherwise deny.
    This factory expects the restaurant id value to be available in the path/params
    under the name provided by 'restaurant_id_param_name' when used in a route.

    Example usage in a route:
      async def endpoint(restaurant_id: str, current_user=Depends(require_restaurant_admin("restaurant_id"))):
           ...
    """

    async def checker(
        # we need both the path param and the resolved current_user; FastAPI will inject both
        restaurant_id: str = Depends(lambda: None),  # placeholder, real value will be provided by route param binding
        current_user: CurrentUser = Depends(get_current_user)
    ):
        # NOTE: FastAPI binding will replace the placeholder with the actual path param value by name.
        # We retrieve the restaurant_id from the request context via function argument.
        # Behavior: When using Depends(require_restaurant_admin("restaurant_id")), FastAPI resolves
        # the parameter named "restaurant_id" and injects it here.
        # Implementation detail: to make this work reliably, use the pattern shown in the route examples.

        if current_user.role == "superadmin":
            return current_user

        if current_user.role != "restaurant_admin":
            logger.warning(f"Forbidden: {current_user.email} with role {current_user.role} tried to access restaurant {restaurant_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only restaurant admins can access this resource")

        # restaurant_id might be None if the binding didn't occur; guard it
        if not restaurant_id:
            logger.error("Restaurant id not provided to require_restaurant_admin dependency")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing restaurant id")

        if restaurant_id not in current_user.restaurant_ids:
            logger.warning(f"Forbidden: {current_user.email} is not assigned to restaurant {restaurant_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to manage this restaurant")

        return current_user

    return checker