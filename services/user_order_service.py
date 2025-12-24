from db.db_operation import mongo_conn
from datetime import datetime
from models.order import OrderCreate, OrderItem
from bson.objectid import ObjectId
from core.exceptions import AppException
from utils.logger import get_logger
from fastapi import HTTPException, status
from typing import List
from pymongo.errors import PyMongoError

logger = get_logger("Order_Service")
# allowed transitions
ALLOWED_TRANSITIONS = {
    "pending": ["accepted", "rejected", "cancelled"],
    "accepted": ["preparing", "cancelled", "rejected"],
    "preparing": ["ready", "cancelled"],
    "ready": ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "rejected": [],
    "cancelled": [],
    "delivered": []
}
USER_CANCELLABLE_STATUSES = [
    "pending",
    "accepted"
]

async def create_order(user_email: str, restaurant_id: str, items: List[OrderItem], status: str = "pending"):
    """
    items: list of {"item_id": "<id>", "quantity": <int>}
    Validations:
      - each item exists and belongs to restaurant_id
      - item is available
    Snapshots:
      - store item_name and price at time of order (so later price changes don't affect historical orders)
    """
    # validate restaurant id
    try:
        ObjectId(restaurant_id)
    except Exception:
        raise ValueError("Invalid restaurant id")

    # Build list of item ObjectIds and map
    item_ids = []
    for it in items:
        try:
            item_ids.append(ObjectId(it.item_id))
        except Exception:
            raise ValueError(f"Invalid item id in items: {it.item_id}")
    # fetch all item docs
    cursor = mongo_conn.menu_items.find({"_id": {"$in": item_ids}})
    found_items = await cursor.to_list(length=None)
    if len(found_items) != len(item_ids):
        raise ValueError("One or more items not found")

    # map by string id
    found_map = {str(d["_id"]): d for d in found_items}

    # ensure all items belong to same restaurant and match requested restaurant_id
    for d in found_items:
        if str(d["restaurant_id"]) != restaurant_id:
            raise ValueError("Item does not belong to specified restaurant")
        if not d.get("is_available", True):
            raise ValueError(f"Item not available: {d['name']}")

    # build order items with snapshot
    order_items = []
    total_amount = 0.0
    for req in items:
        sid = req.item_id
        qty = int(req.quantity)
        doc = found_map.get(sid)
        if doc is None:
            raise ValueError("Item not found in DB: " + sid)
        snapshot = {
            "item_id": sid,
            "item_name": doc["name"],
            "unit_price": float(doc["price"]),
            "quantity": qty,
            "line_total": round(float(doc["price"]) * qty, 2)
        }
        order_items.append(snapshot)
        total_amount += snapshot["line_total"]

    # build order doc
    order_doc = {
        "user_email": user_email,
        "restaurant_id": restaurant_id,
        "items": order_items,
        "total_amount": round(total_amount, 2),
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": None
    }

    try:
        result = await mongo_conn.orders_collection.insert_one(order_doc)
    except PyMongoError as e:
        logger.error(f"Error inserting order: {e}", exc_info=True)
        raise e

    logger.info("Order created", extra={"order_id": str(result.inserted_id), "user": user_email, "restaurant_id": restaurant_id})
    return {
        "id": str(result.inserted_id),
        **order_doc,
        "created_at": order_doc["created_at"].isoformat()
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
    # orders_collection = mongo_conn.orders_collection
    # Convert order_id to ObjectId
    try:
        oid = ObjectId(order_id)
    except Exception:
        logger.error(f"Invalid order ID: {order_id}")
        raise ValueError("Invalid order ID")

    # Check if order exists and belongs to the user
    logger.info(f"Checking if order {order_id} exists and belongs to user {user_email}")
    existing_order = await mongo_conn.orders_collection.find_one({"_id": oid, "user_email": user_email})
    if not existing_order:
        logger.warning(f"Order {order_id} not found or does not belong to user {user_email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found or access denied"
        )

    # Delete the order
    logger.info(f"Deleting order {order_id}")
    result = await mongo_conn.orders_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        logger.warning(f"Order {order_id} could not be deleted")
        raise ValueError("Order could not be deleted")

    logger.info(f"Order {order_id} deleted successfully")
    return {"message": "Order deleted successfully"}

async def update_order_status_by_restaurant(restaurant_id: str, order_id: str, new_status: str, actor_email: str = None, reason: str | None = None):
    # validate ids
    try:
        oid = ObjectId(order_id)
        ObjectId(restaurant_id)
    except Exception:
        raise ValueError("Invalid id")

    order = await mongo_conn.orders.find_one({"_id": oid})
    if not order:
        raise ValueError("Order not found")

    if order.get("restaurant_id") != restaurant_id:
        raise ValueError("Order does not belong to this restaurant")

    current_status = order.get("status")
    if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
        raise ValueError(f"Invalid status transition from {current_status} -> {new_status}")

    update_doc = {"status": new_status, "updated_at": datetime.utcnow()}
    if new_status == "rejected" and reason:
        update_doc["rejection_reason"] = reason

    result = await mongo_conn.orders.update_one({"_id": oid}, {"$set": update_doc})
    if result.matched_count == 0:
        raise ValueError("Failed to update order status")

    # audit
    await mongo_conn.audit_logs.insert_one({
        "actor_email": actor_email,
        "action": "update_order_status",
        "resource_type": "order",
        "resource_id": order_id,
        "before": {"status": current_status},
        "after": {"status": new_status},
        "reason": reason,
        "timestamp": datetime.utcnow()
    })

    logger.info("Order status updated", extra={"order_id": order_id, "from": current_status, "to": new_status, "actor": actor_email})
    return {"order_id": order_id, "from": current_status, "to": new_status}

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

async def cancel_user_order(
    user_email: str,
    order_id: str,
    reason: str | None = None
):
    orders = mongo_conn.orders_collection

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise ValueError("Invalid order id")

    order = await orders.find_one({
        "_id": oid,
        "user_email": user_email
    })

    if not order:
        raise ValueError("Order not found or access denied")

    current_status = order["status"]

    if current_status not in USER_CANCELLABLE_STATUSES:
        raise ValueError(
            f"Order cannot be cancelled in '{current_status}' state"
        )

    update_doc = {
        "status": "cancelled",
        "updated_at": datetime.utcnow(),
        "cancelled_by": "user"
    }

    if reason:
        update_doc["cancellation_reason"] = reason

    await orders.update_one(
        {"_id": oid},
        {"$set": update_doc}
    )

    # AUDIT LOG
    await mongo_conn.audit_logs.insert_one({
        "actor_email": user_email,
        "action": "cancel_order",
        "resource_type": "order",
        "resource_id": order_id,
        "before": {"status": current_status},
        "after": {"status": "cancelled"},
        "reason": reason,
        "timestamp": datetime.utcnow()
    })

    logger.info(
        f"Order {order_id} cancelled by user {user_email}"
    )

    return {
        "order_id": order_id,
        "previous_status": current_status,
        "new_status": "cancelled"
    }
