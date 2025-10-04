from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from db.db_operation import mongo_conn
from models.user import UserOut
import os
from utils.logger import get_logger

logger = get_logger("Security_Utils")



# tells fastapi to expect a token in the request header after login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# JWT Secret & Algorithm
SECRET_KEY = os.getenv("SECRET_KEY", "MySecretKey@123")
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        logger.info("Received request to get current user from token")
        # JWT decode
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token decoded successfully for the current user")
        email: str = payload.get("sub") # sub is used for unique identifier such as email or user id
        logger.info(f"Email found in token: {email}")
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
        
        # UserOut ke format me return karo
        logger.info(f"User found for email: {email}, returning user details")
        return UserOut(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"]
        )

    except JWTError:
        logger.error("JWT Error: Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
