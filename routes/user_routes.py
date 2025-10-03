from fastapi import APIRouter, Depends
from models.user import UserOut
from core.security import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/user", response_model=UserOut)
async def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user
