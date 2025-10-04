from fastapi import APIRouter, Depends, HTTPException, status
from models.order import OrderCreate, OrderOut
from services.order_service import create_order, get_user_orders
from core.security import get_current_user
from typing import List
from utils.logger import get_logger

logger = get_logger("Order_Route")

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderOut)
async def place_order(order: OrderCreate, current_user: str = Depends(get_current_user)):
    """Create a new order"""
    logger.info(f"Received order request: {order}")
    try:
        new_order = await create_order(current_user.email, order)
        return new_order  
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating order")

@router.get("/", response_model=List[OrderOut])
async def get_orders(current_user: str = Depends(get_current_user)):
    """Fetch all orders for current user"""
    try:
        orders = await get_user_orders(current_user)
        return orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching orders")
