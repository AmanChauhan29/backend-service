from motor.motor_asyncio import AsyncIOMotorClient
from settings.config import settings
from utils.logger import get_logger
import asyncio

logger = get_logger("DB_OPERATION")

async def create_indexes():
    orders_collection = mongo_conn.orders_collection
    await orders_collection.create_index("user_email")
    await orders_collection.create_index("status")
    await orders_collection.create_index("restaurant_id")
    logger.info("Indexes created")

class MongoConnection:
    def __init__(self):
        logger.info("Initializing MongoDB Connection")
        mongo_uri = settings.MONGO_URI
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[settings.DB_NAME]
        self.users_collection = self.db["users"]
        self.audit_logs = self.db["audit_logs"]
        self.orders_collection = self.db["orders"]
   
    async def connect(self):
        try:
            # Force an actual connection & authentication check
            await self.db.command("ping")
            logger.info("Successfully connected to MongoDB and authenticated.")
            logger.info(f"Using Database: {settings.DB_NAME}")
            logger.info(f"Collections ready: {self.users_collection.name}, {self.orders_collection.name}")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise e

# Create the instance
mongo_conn = MongoConnection()

# # Ensure connection is verified at startup
# async def verify_db_connection():
#     await mongo_conn.connect()

# Optionally, if you're using FastAPI
# you can hook this into startup event
# Example:
# from fastapi import FastAPI
# app = FastAPI()
#
# @app.on_event("startup")
# async def startup_event():
#     await verify_db_connection()
