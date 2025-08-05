from fastapi import FastAPI
from settings.config import settings
from routes.auth import router as auth_router
from utils.logger import get_logger

logger = get_logger("main")
app = FastAPI()
@app.get("/")
async def health_check():
    logger.info("Health check is successful")
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "message": "FastAPI is running"
    }

app.include_router(auth_router)