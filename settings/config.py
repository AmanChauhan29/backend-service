import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Configuration settings for the application."""
    PROJECT_NAME: str = "Backend API"
    MONGO_URI: str = os.getenv("MONGO_URI")
    DB_NAME: str = os.getenv("DB_NAME")

    class Config:
        env_file = ".env"

settings = Settings()
