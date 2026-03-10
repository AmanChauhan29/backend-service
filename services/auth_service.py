from datetime import datetime, timedelta
from utils.hash import hash_token, hash_password
from utils.token import generate_password_reset_token
from db.db_operation import mongo_conn
from utils.logger import get_logger
from fastapi import HTTPException, BackgroundTasks
from utils.email import send_reset_password_email


logger = get_logger("AUTH_SERVICE")


async def forgot_password(email: str, background_tasks: BackgroundTasks):
    logger.info(f"Password reset requested for email={email}")
    users_collection = mongo_conn.users_collection
    user = await users_collection.find_one({"email": email})
    if not user:
        logger.warning(f"Password reset attempt for non-existent email={email}")
        return {"message": "If account exists, reset email sent"}
    logger.info(f"User found for password reset email={email}")
    reset_token = generate_password_reset_token()
    token_hash = hash_token(reset_token)
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    await users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "reset_password": {
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "used": False,
                    "sent_at": datetime.utcnow()
                }
            }
        }
    )
    logger.info(
        f"Password reset token generated for email={email}, expires_at={expires_at}"
    )
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"
    background_tasks.add_task(
        send_reset_password_email,
        email,
        reset_link
    )
    # send email here
    logger.info(f"RESET TOKEN: {reset_token}")
    return {"message": "Password reset email sent"}

async def reset_password(token: str, new_password: str):
    logger.info("Password reset attempt received")
    users_collection = mongo_conn.users_collection
    token_hash = hash_token(token)
    user = await users_collection.find_one({
        "reset_password.token_hash": token_hash
    })
    if not user:
        logger.warning("Invalid password reset token used")
        raise HTTPException(400, "Invalid reset token")
    reset_data = user["reset_password"]
    if reset_data["used"]:
        logger.warning(
            f"Password reset token already used for email={user['email']}"
        )
        raise HTTPException(400, "Token already used")
    if reset_data["expires_at"] < datetime.utcnow():
        raise HTTPException(400, "Reset token expired")
    logger.info(f"Password reset validated for email={user['email']}")
    hashed_password = hash_password(new_password)
    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hashed_password,
                "reset_password.used": True
            }
        }
    )
    logger.info(f"Password successfully reset for email={user['email']}")
    return {"message": "Password updated successfully"}