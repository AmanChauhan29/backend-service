from datetime import datetime, timedelta
from jose import jwt
from utils.logger import get_logger

logger = get_logger("JWT_HANDLER")

SECRET_KEY = "MySecretKey@123"  # Production: load from env variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict):
    """
    Creates JWT token with expiry.
    """
    logger.info("Access token creation requested")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    logger.info(f"Token will expire at {expire}")
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token created successfully with expiry {expire}")
    return encoded_jwt

def decode_access_token(token: str):
    """
    Decode JWT token and return payload.
    Raises exception if invalid or expired.
    """
    logger.info("Decoding access token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("Token decoded successfully")
        return payload
    except Exception as e:
        raise ValueError("Invalid token")

def create_refresh_token(data: dict):
    """
    Creates JWT token with expiry.
    """
    logger.info("Refresh token creation requested")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    logger.info(f"Token will expire at {expire}")
    to_encode.update({"exp": expire, "iat": datetime.utcnow()}) 
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt