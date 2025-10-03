from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
