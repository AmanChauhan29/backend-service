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
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM") or "HS256"
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL")
    FRONTEND_VERIFY_URL: str = os.getenv("FRONTEND_VERIFY_URL")


    class Config:
        env_file = ".env"

settings = Settings()
