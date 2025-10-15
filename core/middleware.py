from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from utils.logger import get_logger
from core.exceptions import AppException

logger =  get_logger("Middleware")

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            logger.warning(f"AppException: {e.detail}")
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
