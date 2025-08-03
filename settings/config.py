import os
from pydantic import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Configuration settings for the application."""
    PROJECT_NAME: str = "Backend API"
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "testdb")
    age: Optional[int] = Field(default=None)

    class Config:
        env_file = ".env"

settings = Settings()
