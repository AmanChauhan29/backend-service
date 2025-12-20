from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user, CurrentUser
from services.restaurant_order_service import fetch_orders_for_restaurant_admin, update_order_status
from models.order import RestaurantOrderOut, OrderStatusUpdate
from utils.logger import get_logger

logger = get_logger("Restaurant_Order_Service")


router = APIRouter(
    prefix="/restaurant",
    tags=["Restaurant Orders"]
)

@router.get("/orders", response_model=list[RestaurantOrderOut])
async def get_my_restaurant_orders(current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role != "restaurant_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only restaurant admins can access this"
        )
    orders = await fetch_orders_for_restaurant_admin(restaurant_ids=current_user.restaurant_ids)
    return orders

@router.patch("/orders/{order_id}/status")
async def update_my_order_status(
    order_id: str,
    payload: OrderStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    if current_user.role != "restaurant_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only restaurant admins can access this"
        )

    try:
        await update_order_status(
            order_id=order_id,
            new_status=payload.new_status,
            restaurant_ids=current_user.restaurant_ids,
            actor_email=current_user.email
        )
        return {"message": "Order status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
