from fastapi import HTTPException, Request
from utils.logger import get_logger
from fastapi.responses import JSONResponse

logger = get_logger("Global_Exception")

async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception",
        extra={"path": request.url.path}
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)