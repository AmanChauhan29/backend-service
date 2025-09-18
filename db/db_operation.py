from motor.motor_asyncio import AsyncIOMotorClient
from settings.config import settings
from utils.logger import get_logger

logger = get_logger("DB_OPERATION")

class MongoConnection:
    def __init__(self):
        mongo_uri = settings.MONGO_URI
        try: 
            self.client = AsyncIOMotorClient(mongo_uri)
            self.db = self.client[settings.DB_NAME]
            self.users_collection = self.db["users"]
            logger.info("Successfully Connected to MongoDB")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            self.client = None
            self.db = None


