from passlib.context import CryptContext
from utils.logger import get_logger
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = get_logger("HASH_UTILS")

def hash_password(password: str) -> str:
    logger.info(f"Password received for hashing")
    password_str = str(password)  
    if len(password_str.encode('utf-8')) > 72:
        password_str = password_str[:72]
    logger.info(f"Password length after encoding and truncation (if needed): {len(password_str.encode('utf-8'))}")  
    return pwd_context.hash(password_str)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
