from db.db_operation import mongo_conn
from datetime import datetime
from models.order import OrderCreate
from bson.objectid import ObjectId
import logging

logger = logging.getLogger("Order_Service")

async def create_order(user_email: str, order_data: OrderCreate):
    """Create a new order for the logged-in user"""
    logger.info(f"Creating new order for user {user_email}")
    orders_collection = mongo_conn.orders_collection
    logger.info(f"connected to orders collection")
    order_dict = order_data.model_dump()
    order_dict.update({
        "user_email": user_email,
        "created_at": datetime.utcnow()
    })
    result = await orders_collection.insert_one(order_dict)
    logger.info(f"New order created by {user_email} with id {result.inserted_id}")
    return {
        "id": str(result.inserted_id),
        **order_dict
    }


async def get_user_orders(user_email: str):
    """Get all orders of the logged-in user"""
    orders_collection = mongo_conn.orders_collection
    orders_cursor = orders_collection.find({"user_email": user_email})
    orders = await orders_cursor.to_list(None)
    logger.info(f"Fetched {len(orders)} orders for user {user_email}")
    return [
        {
            "id": str(order["_id"]),
            "user_email": order["user_email"],
            "items": order["items"],
            "total_amount": order["total_amount"],
            "status": order["status"],
            "created_at": order["created_at"]
        }
        for order in orders
    ]
