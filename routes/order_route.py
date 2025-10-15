from fastapi import APIRouter, Depends, HTTPException, status
from models.order import OrderCreate, OrderOut
from services.order_service import create_user_order, get_user_orders, update_user_order, delete_user_order
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
        new_order = await create_user_order(current_user.email, order)
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

@router.put("/{order_id}", response_model=OrderOut)
async def update_order(order_id: str, order: OrderCreate, current_user: str = Depends(get_current_user)):
    """Update an existing order"""
    try:
        logger.info(f"Received order update request: {order}")
        updated_order = await update_user_order(current_user.email, order_id, order)
        if not updated_order:
            raise HTTPException(status_code=404, detail="Order not found")
        return updated_order
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating order")

@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: str, current_user: str = Depends(get_current_user)):
    """Delete an existing order"""
    logger.info(f"Received order delete request for order ID: {order_id}")
    try:
        deleted = await delete_user_order(current_user.email, order_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Order not found")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting order")
