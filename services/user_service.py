from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from db.db_operation import mongo_conn
from utils.hash import hash_password, hash_token
from models.user import UserCreate, UserOut
from bson.objectid import ObjectId
from utils.logger import get_logger
from utils.token import create_email_verification_token
from datetime import datetime, timedelta
from jose import jwt,JWTError, ExpiredSignatureError
VERIFY_SECRET_KEY = "VerifySecret@123"
VERIFY_ALGORITHM = "HS256"
VERIFY_TOKEN_EXPIRE_MINUTES = 15
VERIFICATION_RESEND_COOLDOWN_MINUTES = 1
logger = get_logger("USER_SERVICE")

async def create_user(user: UserCreate):
    logger.info(f"User create request received for email: {user.email}")
    users_collection = mongo_conn.users_collection
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    verify_token = create_email_verification_token(user.email)
    if verify_token is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate verification token")
    logger.info(
        "Verification token generated",
        extra={"email": user.email}
    )
    token_hash = hash_token(verify_token)

    user_dict = {
        "email": user.email,
        "full_name": user.full_name,
        "password": hash_password(user.password),  # hashed password
        "role": "user",                              # default role
        "restaurant_ids": [],                        # default empty
        "token_version": 0,                          # default token version
        "created_at": datetime.utcnow(),
        "is_verified": False,
        "verification": {
            "token_hash": token_hash,
            "expires_at": datetime.utcnow() + timedelta(minutes=VERIFY_TOKEN_EXPIRE_MINUTES),
            "used": False
        },
        "verified_at": None,
        "verification_sent_at": datetime.utcnow(),
        "status": "pending"
    }
    result =  await users_collection.insert_one(user_dict)
    logger.info(f"User inserted into database with id: {result.inserted_id}")
    return verify_token

async def verify_user_email(token: str):
    logger.info("Email verification attempt")
    try:
        payload = jwt.decode(token, VERIFY_SECRET_KEY, algorithms=[VERIFY_ALGORITHM])
        if payload.get("purpose") != "email_verification":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token purpose")
        email = payload.get("sub")
        token_hash = hash_token(token)
        user = await mongo_conn.users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User associated with this token does not exist")
        verification = user.get("verification")

        if not verification:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification data missing")

        if verification["used"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already verified")

        if verification["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired. Please request a new one.")

        if verification["token_hash"] != token_hash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token.")

        # ✅ Mark verified
        await mongo_conn.users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "is_verified": True,
                    "status": "active",
                    "verified_at": datetime.utcnow(),
                    "verification.used": True
                }
            }
        )
        return {"message": "Email verified successfully."}
    except ExpiredSignatureError:
        logger.warning("Verification token has expired")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Verification link has expired. Please request a new one."
        )
    except JWTError:
        logger.warning("Invalid verification token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )
    
async def resend_verification_email(email: str):
    user = await mongo_conn.users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )

    if user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified"
        )

    verification = user.get("verification")

    # ⏳ Rate-limit resend
    if verification:
        last_sent = verification.get("sent_at")
        if last_sent and datetime.utcnow() - last_sent < timedelta(minutes=VERIFICATION_RESEND_COOLDOWN_MINUTES):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification email"
            )

    # 🔐 Generate new token
    token = create_email_verification_token(email)
    token_hash = hash_token(token)

    verification_doc = {
        "token_hash": token_hash,
        "expires_at": datetime.utcnow() + timedelta(minutes=15),
        "used": False,
        "sent_at": datetime.utcnow()
    }

    await mongo_conn.users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "verification": verification_doc
            }
        }
    )

    logger.info("Verification email resent", extra={"email": email})

    return token