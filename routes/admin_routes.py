# routes/admin_routes.py (skeleton)
from fastapi import APIRouter, Depends, HTTPException, status
from core.authorization import require_role
from db.db_operation import mongo_conn
from utils.logger import get_logger

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger("Admin_Route")

@router.post("/users/{user_email}/revoke")
async def revoke_user_tokens(user_email: str, current_admin = Depends(require_role("superadmin"))):
    users = mongo_conn.users_collection
    result = await users.update_one({"email": user_email}, {"$inc": {"token_version": 1}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"User tokens revoked by {current_admin.email} for {user_email}")
    return {"message": "User tokens revoked"}
