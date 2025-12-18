from pydantic import BaseModel, Field, PositiveInt
from typing import Optional
from datetime import datetime

class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    is_available: bool = True

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None

class MenuItemOut(BaseModel):
    id: str
    restaurant_id: str
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class OrderItemIn(BaseModel):
    item_id: str
    quantity: PositiveInt = Field(1, gt=0)
