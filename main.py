from fastapi import FastAPI
from settings.config import settings
from db.db_operation import create_indexes
from utils.logger import get_logger
from routes import order_route, user_routes, auth
# from core.middleware import ExceptionHandlerMiddleware

logger = get_logger("main")

app = FastAPI(title="Food Ordering System API", version="1.0.0")
@app.get("/")
async def health_check():
    logger.info("Health check is successful")
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "message": "FastAPI is running"
    }
@app.on_event("startup")
async def startup_event():
    await create_indexes()
# app.add_middleware(ExceptionHandlerMiddleware)
app.include_router(auth.router)
app.include_router(user_routes.router)
app.include_router(order_route.router)