from db.db_operation import mongo_conn
from datetime import datetime
from bson import ObjectId
from typing import List
from utils.logger import get_logger 
logger = get_logger("Restaurant_Order_Service")
ALLOWED_STATUS_TRANSITIONS = {
    "pending": ["preparing"],
    "preparing": ["ready"],
    "ready": ["delivered"],
    "delivered": []
}


async def fetch_orders_for_restaurant_admin(restaurant_ids: list):
    orders_collection = mongo_conn.orders_collection
    cursor = orders_collection.find({
        "restaurant_id": {"$in": restaurant_ids}
    })
    orders = await cursor.to_list(length=None)
    return orders

async def update_order_status(
order_id: str,
    new_status: str,
    restaurant_ids: list[str],
    actor_email: str
):
    orders_collection = mongo_conn.orders_collection
    order = await orders_collection.find_one({
        "_id": ObjectId(order_id),
        "restaurant_id": {"$in": restaurant_ids}
    })

    if not order:
        raise ValueError("Order not found or access denied")

    current_status = order["status"]

    if new_status not in ALLOWED_STATUS_TRANSITIONS.get(current_status, []):
        raise ValueError(
            f"Invalid status transition from {current_status} to {new_status}"
        )

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.utcnow(),
                "updated_by": actor_email
            }
        }
    )
    await mongo_conn.audit_logs.insert_one({
        "actor_email": actor_email,
        "action": "update_order_status",
        "resource_type": "order",
        "resource_id": order_id,
        "before": {"status": current_status},
        "after": {"status": new_status},
        "timestamp": datetime.utcnow()
    })
    logger.info(
        "Order status updated",
        extra={"order_id": order_id, "from": current_status, "to": new_status, "by": actor_email}
    )   

    return True