from fastapi import HTTPException, status
from db.db_operation import mongo_conn
from utils.hash import hash_password
from models.user import UserCreate, UserOut
from bson.objectid import ObjectId
from utils.logger import get_logger
from utils.token import create_email_verification_token
from datetime import datetime


logger = get_logger("USER_SERVICE")

async def create_user(user: UserCreate):
    logger.info(f"User create request received for email: {user.email}")
    users_collection = mongo_conn.users_collection
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_dict = {
        "email": user.email,
        "full_name": user.full_name,
        "password": hash_password(user.password),  # hashed password
        "role": "user",                              # default role
        "restaurant_ids": [],                        # default empty
        "token_version": 0,                          # default token version
        "created_at": datetime.utcnow(),
        "is_verified": False,
        "verified_at": None,
        "verification_sent_at": datetime.utcnow(),
        "status": "pending"
    }
    result =  await users_collection.insert_one(user_dict)
    logger.info(f"User inserted into database with id: {result.inserted_id}")
    verify_token = create_email_verification_token(user.email)
    logger.info(
        "Verification token generated",
        extra={"email": user.email}
    )
    return verify_token
