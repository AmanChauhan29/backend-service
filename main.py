from fastapi import FastAPI
from settings.config import settings


app = FastAPI()
@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "message": "FastAPI is running"
    }