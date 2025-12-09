from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    

class UserInDB(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "user"
    restaurant_ids: List[str] = []
    token_version: int = 0

class UserOut(BaseModel):
    email: str
    role: str
    restaurant_ids: List[str] = []
    token_version: int = 0
    full_name: str | None = None
    id: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str