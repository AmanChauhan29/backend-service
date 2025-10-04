from motor.motor_asyncio import AsyncIOMotorClient
from settings.config import settings
from utils.logger import get_logger

logger = get_logger("DB_OPERATION")

class MongoConnection:
    def __init__(self):
        logger.info("Initializing MongoDB Connection")
        mongo_uri = settings.MONGO_URI
        try: 
            self.client = AsyncIOMotorClient(mongo_uri)
            logger.info("Successfully Connected to MongoDB")
            self.db = self.client[settings.DB_NAME]
            logger.info(f"Using Database: {settings.DB_NAME}")
            self.users_collection = self.db["users"]
            self.orders_collection = self.db["orders"]
            logger.info(f"Successfully Connected to MongoDB Database and Collection {self.users_collection}, {self.orders_collection}")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB due to error: {e}")
            raise e
mongo_conn = MongoConnection()

