from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RefreshToken(BaseModel):
    user_email: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    revoked: bool = False
    replaced_by_token: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str