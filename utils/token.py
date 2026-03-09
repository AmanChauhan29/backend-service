from jose import jwt
from datetime import datetime, timedelta
import os

VERIFY_SECRET_KEY = "VerifySecret@123"
VERIFY_ALGORITHM = "HS256"
VERIFY_TOKEN_EXPIRE_MINUTES = 15

def create_email_verification_token(email: str) -> str:
    """
    Creates short-lived JWT for email verification
    """
    payload = {
        "sub": email,
        "purpose": "email_verification",
        "exp": datetime.utcnow() + timedelta(minutes=VERIFY_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, VERIFY_SECRET_KEY, algorithm=VERIFY_ALGORITHM)
    return token

