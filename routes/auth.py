from fastapi import APIRouter, HTTPException, status
from models.user import UserCreate, UserOut
from pymongo.errors import PyMongoError
from services.user_service import create_user
from utils.logger import get_logger

logger = get_logger("AUTH_ROUTE")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    logger.info(f"Attempting to sign up user with email: {user.email}")
    try:
        user_created = await create_user(user)
        logger.info(f"User created with email: {user.email}")
        return user_created
    except ValueError as e:
        logger.error(f"Error during user signup: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PyMongoError as e:
        logger.error(f"Database error during user signup: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error during user signup: {e}")   
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")