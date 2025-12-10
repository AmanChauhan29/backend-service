# models/restaurant.py
from pydantic import BaseModel, Field
from typing import Optional, List

class RestaurantCreate(BaseModel):
    name: str = Field(min_length=2)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    # initial owner (for superadmin create). Normal public signup should not set this.
    owner_email: Optional[str] = None

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class RestaurantOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    slug: Optional[str] = None
    owner_email: Optional[str] = None
    approved: bool = False
    disabled: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class RestaurantListItem(RestaurantOut):
    pass
