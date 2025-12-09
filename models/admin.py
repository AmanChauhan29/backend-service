# models/admin.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# Request payload to change a user's role
class RoleChangeRequest(BaseModel):
    role: str
    restaurant_ids: List[str] = Field(default_factory=list)
    reason: Optional[str] = None

# Response for listing users
class UserListItem(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    restaurant_ids: List[str] = Field(default_factory=list)
    disabled: bool = False

# Response for user details
class UserDetail(UserListItem):
    token_version: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Response for audit log item
class AuditItem(BaseModel):
    id: str
    actor_email: str
    action: str
    resource_type: str
    resource_id: str
    before: Optional[dict] = None
    after: Optional[dict] = None
    reason: Optional[str] = None
    timestamp: str
