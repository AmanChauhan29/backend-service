from db.db_operation import mongo_conn
from utils.hash import hash_password
from models.user import UserCreate
from bson.objectid import ObjectId
from utils.logger import get_logger

logger = get_logger("USER_SERVICE")

async def create_user(user: UserCreate):
    logger.info(f"User create request received for email: {user.email}")
    users_collection = mongo_conn.users_collection
    if await users_collection.find_one({"email": user.email}):
        logger.warning(f"Attempt to create a user with existing email: {user.email}")
        raise ValueError("Email already registered")

    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user.password)
    logger.info(f"Password hashed for user email: {user.email}")
    result =  await users_collection.insert_one(user_dict)
    logger.info(f"User inserted into database with id: {result.inserted_id}")
    return {
        "id": str(result.inserted_id),
        "email": user.email,
        "full_name": user.full_name
    }
