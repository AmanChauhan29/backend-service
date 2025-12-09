# routes/admin_routes.py (skeleton)
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from core.authorization import require_role
from db.db_operation import mongo_conn
from utils.logger import get_logger
from pydantic import BaseModel
from services.admin_service import promote_user_to_restaurant_admin, list_users, get_user_by_id
from core.dependencies import get_current_user
from models.admin import UserListItem, UserDetail, AuditItem, RoleChangeRequest
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger("Admin_Route")

class PromotePayload(BaseModel):
    restaurant_ids: list[str] = []

@router.get("/users", response_model=List[UserListItem], dependencies=[Depends(require_role("superadmin"))])
async def list_all_users(skip: int = Query(0, ge=0), limit: int = Query(50, le=200)):
    """
    List users (superadmin only). Pagination supported via skip & limit.
    """
    return await list_users(skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=UserDetail, dependencies=[Depends(require_role("superadmin"))])
async def api_get_user(user_id: str = Path(..., description="User ObjectId string")):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/users/{user_email}/revoke")
async def revoke_user_tokens(user_email: str, current_admin = Depends(require_role("superadmin"))):
    users = mongo_conn.users_collection
    result = await users.update_one({"email": user_email}, {"$inc": {"token_version": 1}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"User tokens revoked by {current_admin.email} for {user_email}")
    return {"message": "User tokens revoked"}


@router.post("/users/{target_email}/promote", dependencies=[Depends(require_role("superadmin"))])
async def promote_user(target_email: str, payload: PromotePayload, current_admin = Depends(get_current_user)):
    """
    Promote a user to restaurant_admin and assign restaurant ids.
    Only accessible by superadmin.
    """
    try:
        res = await promote_user_to_restaurant_admin(target_email, payload.restaurant_ids, current_admin.email)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception("Error promoting user")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")