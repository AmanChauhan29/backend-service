from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from models.user import UserCreate, UserOut, UserLogin
from db.db_operation import mongo_conn
from pymongo.errors import PyMongoError
from utils.email import send_verification_email
from utils.hash import verify_password
from utils.jwt_handler import create_access_token
from services.user_service import create_user, verify_user_email, resend_verification_email
from utils.logger import get_logger
import os
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("AUTH_ROUTE")

router = APIRouter(prefix="/auth", tags=["Authentication"])
FRONTEND_VERIFY_URL = os.getenv("FRONTEND_VERIFY_URL")

@router.post("/signup")
async def signup(user: UserCreate, background_tasks: BackgroundTasks):
    logger.info(f"Attempting to sign up user with email: {user.email}")
    try:
        verify_token = await create_user(user)
        verify_link = f"{FRONTEND_VERIFY_URL}?token={verify_token}"
        # async email send
        background_tasks.add_task(
            send_verification_email,
            user.email,
            verify_link
        )
        logger.info(f"Soft User created with email: {user.email}")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
            "message": "User created successfully. Please check your email to verify your account.",
            "email": user.email
        })
    except ValueError as e:
        logger.error(f"Error during user signup: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PyMongoError as e:
        logger.error(f"Database error during user signup: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error during user signup: {e}")   
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    
@router.get("/verify-email")
async def verify_email(token: str):
    logger.info("Email verification request received")
    return await verify_user_email(token)

@router.post("/resend-verification")
async def resend_verification(
    email: str,
    background_tasks: BackgroundTasks
):
    token = await resend_verification_email(email)

    verify_link = f"{FRONTEND_VERIFY_URL}?token={token}"

    background_tasks.add_task(
        send_verification_email,
        email,
        verify_link
    )

    return {
        "message": "Verification email resent successfully"
    }


@router.post("/login")
async def login(user: UserLogin):
    logger.info(f"Login attempt for: {user.email}")
    users_collection = mongo_conn.users_collection
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        logger.warning(f"Login failed: user not found {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    if db_user.get("disabled", False):
    # Reason: user account is administratively disabled
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled. Contact support.")
    
    if not verify_password(user.password, db_user["password"]):
        logger.warning(f"Login failed: wrong password {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"id": str(db_user["_id"]), "sub": db_user["email"], "role": db_user["role"], "token_version": db_user["token_version"], "restaurant_ids": db_user["restaurant_ids"]})
    logger.info(f"Login successful: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}