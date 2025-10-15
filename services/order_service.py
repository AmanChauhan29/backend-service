from db.db_operation import mongo_conn
from datetime import datetime
from models.order import OrderCreate
from bson.objectid import ObjectId
from core.exceptions import AppException
from utils.logger import get_logger
from fastapi import HTTPException, status

logger = get_logger("Order_Service")

async def create_user_order(user_email: str, order_data: OrderCreate):
    """Create a new order for the logged-in user"""
    logger.info(f"Creating new order for user {user_email}")
    orders_collection = mongo_conn.orders_collection
    logger.info(f"connected to orders collection")
    if not order_data.items:
        raise AppException(status_code=400, detail="Order must have at least one item")
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

async def update_user_order(user_email: str, order_id: str, order_data: OrderCreate):
    """Update an existing order for the logged-in user"""
    logger.info(f"Attempting to update order {order_id} for user {user_email}")
    orders_collection = mongo_conn.orders_collection
    # Convert order_id to ObjectId
    try:
        oid = ObjectId(order_id)
    except Exception as e:
        logger.error(f"Invalid order ID: {order_id}")
        raise ValueError("Invalid order ID")
    # Check if order exists and belongs to the user
    logger.info(f"Checking if order {order_id} exists and belongs to user {user_email}")
    existing_order = await orders_collection.find_one({"_id": oid, "user_email": user_email})
    if not existing_order:
        logger.warning(f"Order {order_id} not found or does not belong to user {user_email}")
        raise ValueError("Order not found or access denied")

    # Prepare updated data
    update_data = order_data.model_dump()
    update_data["updated_at"] = datetime.utcnow()
    logger.info(f"Updating order {order_id} with data: {update_data}")
    # Perform update
    result = await orders_collection.update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        logger.warning(f"No changes were made to order {order_id}")
    else:
        logger.info(f"Order {order_id} updated successfully")

    # Return updated order
    updated_order = await orders_collection.find_one({"_id": oid})
    return {
        "id": str(updated_order["_id"]),
        "user_email": updated_order["user_email"],
        "items": updated_order["items"],
        "total_amount": updated_order["total_amount"],
        "status": updated_order["status"],
        "created_at": updated_order["created_at"],
        "updated_at": updated_order.get("updated_at")
    }

async def delete_user_order(user_email: str, order_id: str):
    """Delete an existing order for the logged-in user"""
    logger.info(f"Attempting to delete order {order_id} for user {user_email}")
    orders_collection = mongo_conn.orders_collection
    # Convert order_id to ObjectId
    try:
        oid = ObjectId(order_id)
    except Exception:
        logger.error(f"Invalid order ID: {order_id}")
        raise ValueError("Invalid order ID")

    # Check if order exists and belongs to the user
    logger.info(f"Checking if order {order_id} exists and belongs to user {user_email}")
    existing_order = await orders_collection.find_one({"_id": oid, "user_email": user_email})
    if not existing_order:
        logger.warning(f"Order {order_id} not found or does not belong to user {user_email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found or access denied"
        )

    # Delete the order
    logger.info(f"Deleting order {order_id}")
    result = await orders_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        logger.warning(f"Order {order_id} could not be deleted")
        raise ValueError("Order could not be deleted")

    logger.info(f"Order {order_id} deleted successfully")
    return {"message": "Order deleted successfully"}
