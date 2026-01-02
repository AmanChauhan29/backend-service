import time
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from db.redis_client import redis_client
from utils.logger import get_logger
import os
from settings.config import settings
logger = get_logger("RedisRateLimit")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

class RedisRateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app,
        requests: int = 100,
        window_seconds: int = 60
    ):
        super().__init__(app)
        self.requests = requests
        self.window = window_seconds
        self.exclude_paths = {
            "/auth/login",
            "/docs",
            "/openapi.json"
        }

    def _get_identity(self, request: Request) -> str:
        """
        Priority:
        1. JWT email (logged-in user)
        2. Client IP
        """
        auth = request.headers.get("Authorization")
        if not auth:
            return request.client.host

        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub", request.client.host)
        except JWTError:
            return request.client.host

    async def dispatch(self, request: Request, call_next):
        identity = self._get_identity(request)
        now = int(time.time())
        window_key = now // self.window
        redis_key = f"rate:{identity}:{window_key}"

        try:
            current_count = await redis_client.incr(redis_key)

            if current_count == 1:
                await redis_client.expire(redis_key, self.window)

            if current_count > self.requests:
                logger.warning(
                    "Rate limit exceeded",
                    extra={"identity": identity, "count": current_count}
                )
                # 🔥 IMPORTANT: do NOT catch this
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests, please slow down"}
                )
        except Exception as e:
            # ✅ Only Redis/network errors
            logger.error("Redis rate limit error", exc_info=e)
            # fail-open → allow request

        return await call_next(request)
