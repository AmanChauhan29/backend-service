from db.db_operation import users_collection
from utils.hash import hash_password
from models.user import UserCreate
from bson.objectid import ObjectId

def create_user(user: UserCreate):
    if users_collection.find_one({"email": user.email}):
        raise ValueError("Email already registered")

    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user.password)
    
    result =  users_collection.insert_one(user_dict)
    return {
        "id": str(result.inserted_id),
        "email": user.email,
        "full_name": user.full_name
    }
