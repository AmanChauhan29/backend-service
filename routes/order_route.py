from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.order import OrderCreate, OrderOut, PaginatedOrderResponse
from services.order_service import create_user_order, get_user_orders, update_user_order, delete_user_order, update_order_status, list_user_orders
from core.dependencies import get_current_user
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

@router.get("/", response_model=PaginatedOrderResponse)
async def get_orders(
                    current_user: str = Depends(get_current_user),
                    status: str | None = Query(None, description="Filter by order status"),
                    page: int = Query(1, ge=1, description="Page number"),
                    limit: int = Query(10, ge=1, le=50, description="Number of results per page")
                    ):
    """Fetch all orders for current user"""
    try:
        orders = await list_user_orders(current_user.email, status, page, limit)
        return orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching orders")

@router.put("/{order_id}", response_model=OrderOut)
async def update_order(order_id: str, order: OrderCreate, current_user: str = Depends(get_current_user)):
    """Update an existing order"""
    logger.info(f"Received update request for order {order_id} from user {current_user.email}")
    try:
        updated_order = await update_user_order(current_user.email, order_id, order)
        if not updated_order:
            raise HTTPException(status_code=404, detail="Order not found")
        return updated_order
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {e}", exc_info=True)
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

@router.patch("/{order_id}/status")
async def change_order_status(order_id: str, status: str, current_user: str = Depends(get_current_user)):
    """
    Change order status if allowed (pending → preparing → dispatched → delivered)
    """
    logger.info(f"Received status update request for {order_id} → {status} from {current_user.email}")
    try:
        response = await update_order_status(current_user.email, order_id, status)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating status for {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")