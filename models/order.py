from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderItem(BaseModel):
    item_name: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    items: List[OrderItem]
    total_amount: float
    status: str = Field(default="pending")

class OrderOut(BaseModel):
    id: str
    user_email: str
    items: List[OrderItem]
    total_amount: float
    status: str
    created_at: datetime
