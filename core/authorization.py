# core/authorization.py
from fastapi import Depends, HTTPException, status
from core.dependencies import get_current_user, CurrentUser
from utils.logger import get_logger

logger = get_logger("Authorization")

def require_role(*allowed_roles):
    async def _dependency(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            logger.warning(f"Forbidden: {current_user.email} role {current_user.role} not in allowed {allowed_roles}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: insufficient role")
        return current_user
    return _dependency
