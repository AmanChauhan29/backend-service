from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user, CurrentUser
from services.restaurant_order_service import fetch_orders_for_restaurant_admin
from models.order import RestaurantOrderOut
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