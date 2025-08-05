from motor.motor_asyncio import AsyncIOMotorClient
from settings.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
users_collection = db["users"]
