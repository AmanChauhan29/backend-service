# routes/restaurant_routes.py
from fastapi import APIRouter, Depends
from core.dependencies import require_restaurant_admin, get_current_user
from db.db_operation import mongo_conn

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

@router.get("/{restaurant_id}/orders")
async def get_restaurant_orders(
    restaurant_id: str,
    current_user = Depends(require_restaurant_admin("restaurant_id"))
):
    orders_col = mongo_conn.orders_collection
    cursor = orders_col.find({"restaurant_id": restaurant_id}).sort("created_at", -1)
    orders = await cursor.to_list(100)
    return [{"id": str(o["_id"]), "user_email": o["user_email"], "items": o["items"], "status": o["status"]} for o in orders]
