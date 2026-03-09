from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from models.user import UserCreate, UserOut, UserLogin
from db.db_operation import mongo_conn
from pymongo.errors import PyMongoError
from utils.email import send_verification_email
from utils.hash import verify_password, hash_token
from utils.jwt_handler import create_access_token, get_refresh_token_expiry
from services.user_service import create_user, verify_user_email, resend_verification_email
from utils.logger import get_logger
import os
from datetime import datetime, timedelta
import secrets
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
async def login(user: UserLogin, request: Request):
    logger.info(f"Login attempt for: {user.email}")
    users_collection = mongo_conn.users_collection
    refresh_tokens_collection = mongo_conn.refresh_tokens_collection
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        logger.warning(f"Login failed: user not found {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not db_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    if db_user.get("disabled", False):
    # Reason: user account is administratively disabled
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled. Contact support.")
    
    if not verify_password(user.password, db_user["password"]):
        logger.warning(f"Login failed: wrong password {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"id": str(db_user["_id"]), "sub": db_user["email"], "role": db_user["role"], "token_version": db_user["token_version"], "restaurant_ids": db_user["restaurant_ids"]})
    refresh_token = secrets.token_urlsafe(64)
    token_hash = hash_token(refresh_token)
    refresh_token_doc = {
        "user_email": db_user["email"],
        "token_hash": token_hash,
        "created_at": datetime.utcnow(),
        "expires_at": get_refresh_token_expiry(),
        "revoked": False,
        "replaced_by_token": None,
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host
    }
    await refresh_tokens_collection.insert_one(refresh_token_doc)
    logger.info(f"Login successful: {user.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_access_token(refresh_token: str):

    refresh_tokens_collection = mongo_conn.refresh_tokens_collection
    users_collection = mongo_conn.users_collection

    token_hash = hash_token(refresh_token)

    token_doc = await refresh_tokens_collection.find_one({
        "token_hash": token_hash
    })

    if not token_doc:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # ---------------- REUSE DETECTION ---------------- #

    if token_doc["revoked"]:

        if token_doc.get("replaced_by_token"):

            # reuse detected
            await refresh_tokens_collection.update_many(
                {"user_email": token_doc["user_email"]},
                {"$set": {"revoked": True}}
            )

            raise HTTPException(
                status_code=401,
                detail="Token reuse detected. All sessions revoked."
            )

        raise HTTPException(
            status_code=401,
            detail="Refresh token revoked"
        )

    # ---------------- EXPIRY CHECK ---------------- #

    if token_doc["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired"
        )

    user = await users_collection.find_one({
        "email": token_doc["user_email"]
    })

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ---------------- ROTATION ---------------- #

    new_refresh_token = secrets.token_urlsafe(64)
    new_token_hash = hash_token(new_refresh_token)

    await refresh_tokens_collection.update_one(
        {"_id": token_doc["_id"]},
        {
            "$set": {
                "revoked": True,
                "replaced_by_token": new_token_hash
            }
        }
    )

    new_token_doc = {
        "user_email": user["email"],
        "token_hash": new_token_hash,
        "created_at": datetime.utcnow(),
        "expires_at": get_refresh_token_expiry(),
        "revoked": False,
        "replaced_by_token": None
    }

    await refresh_tokens_collection.insert_one(new_token_doc)

    access_token = create_access_token({
        "id": str(user["_id"]),
        "sub": user["email"],
        "role": user["role"],
        "token_version": user["token_version"],
        "restaurant_ids": user["restaurant_ids"]
    })

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }