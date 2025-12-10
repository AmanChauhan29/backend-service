# scripts/seed_superadmin.py
import asyncio
from db.db_operation import mongo_conn
from utils.hash import hash_password
from datetime import datetime

async def seed():
    users = mongo_conn.users_collection
    # ensure all existing users have role and token_version
    await users.update_many({}, {"$set": {"role": "user", "token_version": 0, "restaurant_ids": []}})
    # create superadmin if not exists
    admin_email = "superadmin@platform.com"
    existing = await users.find_one({"email": admin_email})
    if not existing:
        admin_doc = {
            "email": admin_email,
            "full_name": "Platform SuperAdmin",
            "password": hash_password("Admin@123"),
            "role": "superadmin",
            "restaurant_ids": [],
            "token_version": 0,
            "created_at": datetime.utcnow()
        }
        result = await users.insert_one(admin_doc)
        print("Created superadmin:", admin_email, result.inserted_id)
    else:
        print("Superadmin already exists")

if __name__ == "__main__":
    asyncio.run(seed())
