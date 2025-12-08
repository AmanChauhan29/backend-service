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
        role: str = payload.get("role", "user")
        rid = payload.get("rid", [])
        tv = int(payload.get("tv", 0))

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
        db_tv = user.get("token_version", 0)
        if db_tv != tv:
            logger.warning(f"Token version mismatch for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        current_user = CurrentUser(
            email=user.get("email"),
            role=user.get("role", "user"),
            restaurant_ids=user.get("restaurant_ids", []),
            token_version=user.get("token_version", 0),
            full_name=user.get("full_name", None),
            id=str(user.get("_id", None))
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
