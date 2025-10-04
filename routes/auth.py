from fastapi import APIRouter, HTTPException, status
from models.user import UserCreate, UserOut, UserLogin
from db.db_operation import mongo_conn
from pymongo.errors import PyMongoError
from utils.hash import verify_password
from utils.jwt_handler import create_access_token
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
    
@router.post("/login")
async def login(user: UserLogin):
    logger.info(f"Login attempt for: {user.email}")
    users_collection = mongo_conn.users_collection
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        logger.warning(f"Login failed: user not found {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password(user.password, db_user["password"]):
        logger.warning(f"Login failed: wrong password {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"id": str(db_user["_id"]), "sub": db_user["email"]})
    logger.info(f"Login successful: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}