from db.db_operation import mongo_conn
from datetime import datetime
from models.order import OrderCreate
from bson.objectid import ObjectId
from core.exceptions import AppException
from utils.logger import get_logger
from fastapi import HTTPException, status

logger = get_logger("Order_Service")
ALLOWED_STATUS_TRANSITIONS = {
    "pending": ["preparing", "cancelled"],
    "preparing": ["dispatched", "cancelled"],
    "dispatched": ["delivered"],
    "delivered": [],
    "cancelled": []
}
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

async def update_user_order(user_email: str, order_id: str, order_data):
    """Update an order only if it belongs to the current user"""    
    orders_collection = mongo_conn.orders_collection
    logger.info(f"User {user_email} requested update for order {order_id}")

    # Validate order_id
    try:
        oid = ObjectId(order_id)
    except Exception:
        logger.error(f"Invalid Order ID format: {order_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Order ID format"
        )

    # Check if order exists and belongs to user
    existing_order = await orders_collection.find_one({"_id": oid, "user_email": user_email})
    if not existing_order:
        logger.warning(f"Order {order_id} not found or access denied for user {user_email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied"
        )

    # Convert Pydantic model to dict
    order_dict = order_data.model_dump()
    order_dict["updated_at"] = datetime.utcnow()

    # Update order in DB
    result = await orders_collection.update_one(
        {"_id": oid, "user_email": user_email},
        {"$set": order_dict}
    )

    if result.modified_count == 0:
        logger.warning(f"No changes made for order {order_id}")
    else:
        logger.info(f"Order {order_id} updated successfully for user {user_email}")

    # Return the updated order
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

async def update_order_status(user_email: str, order_id: str, new_status: str):
    """Update order status following valid transitions"""
    orders_collection = mongo_conn.orders_collection
    logger.info(f"User {user_email} requested status change for order {order_id} → {new_status}")

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    # Fetch existing order
    order = await orders_collection.find_one({"_id": oid, "user_email": user_email})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or access denied")

    current_status = order["status"]

    # Check valid transition
    if new_status not in ALLOWED_STATUS_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from '{current_status}' to '{new_status}'"
        )

    # Update status
    await orders_collection.update_one(
        {"_id": oid},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )

    logger.info(f"Order {order_id} status updated from {current_status} → {new_status}")
    return {"message": f"Order status changed from {current_status} to {new_status}"}

async def list_user_orders(user_email: str, status: str | None = None, page: int = 1, limit: int = 10):
    """Fetch paginated user orders with optional status filter"""
    orders_collection = mongo_conn.orders_collection

    query = {"user_email": user_email}
    if status:
        query["status"] = status

    skip = (page - 1) * limit

    cursor = orders_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)

    total_count = await orders_collection.count_documents(query)

    return {
        "total_orders": total_count,
        "page": page,
        "page_size": limit,
        "orders": [
            {
                "id": str(order["_id"]),
                "user_email": order["user_email"],
                "items": order["items"],
                "total_amount": order["total_amount"],
                "status": order["status"],
                "created_at": order["created_at"],
                "updated_at": order.get("updated_at")
            } for order in orders
        ]
    }
