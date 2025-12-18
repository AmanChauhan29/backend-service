from db.db_operation import mongo_conn
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
from utils.logger import get_logger

logger = get_logger("Menu_Service")

async def create_menu_item(restaurant_id: str, payload, actor_email: str = None):
    """
    Create a menu item for a restaurant. Enforce unique (restaurant_id + name).
    """
    
    try:
        rid = ObjectId(restaurant_id)
    except Exception:
        raise ValueError("Invalid restaurant id")

    now = datetime.utcnow()
    doc = {
        "restaurant_id": restaurant_id,
        "name": payload.name,
        "description": payload.description,
        "price": float(payload.price),
        "is_available": bool(payload.is_available),
        "created_at": now,
        "updated_at": now
    }
    try:
        result = await mongo_conn.menu_items.insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Menu item with same name already exists for this restaurant")
    except PyMongoError:
        logger.exception("DB error creating menu item")
        raise

    logger.info("Menu item created", extra={"restaurant_id": restaurant_id, "actor": actor_email, "item_id": str(result.inserted_id)})
    return {
        "id": str(result.inserted_id),
        "restaurant_id": restaurant_id,
        "name": doc["name"],
        "description": doc.get("description"),
        "price": doc["price"],
        "is_available": doc["is_available"],
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat()
    }

async def list_menu_items(restaurant_id: str, only_available: bool = True):
    try:
        ObjectId(restaurant_id)
    except Exception:
        raise ValueError("Invalid restaurant id")

    q = {"restaurant_id": restaurant_id}
    if only_available:
        q["is_available"] = True

    cursor = mongo_conn.menu_items.find(q).sort("name", 1)
    docs = await cursor.to_list(length=None)
    out = []
    for d in docs:
        out.append({
            "id": str(d["_id"]),
            "restaurant_id": d["restaurant_id"],
            "name": d["name"],
            "description": d.get("description"),
            "price": d["price"],
            "is_available": d.get("is_available", True),
            "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
            "updated_at": d.get("updated_at").isoformat() if d.get("updated_at") else None
        })
    return out

async def get_menu_item(restaurant_id: str, item_id: str):
    try:
        ObjectId(item_id)
    except Exception:
        raise ValueError("Invalid item id")
    d = await mongo_conn.menu_items.find_one({"_id": ObjectId(item_id), "restaurant_id": restaurant_id})
    if not d:
        return None
    return {
        "id": str(d["_id"]),
        "restaurant_id": d["restaurant_id"],
        "name": d["name"],
        "description": d.get("description"),
        "price": d["price"],
        "is_available": d.get("is_available", True),
        "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
        "updated_at": d.get("updated_at").isoformat() if d.get("updated_at") else None
    }

async def update_menu_item(restaurant_id: str, item_id: str, payload, actor_email: str = None):
    try:
        oid = ObjectId(item_id)
    except Exception:
        raise ValueError("Invalid item id")
    update_doc = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "price" in update_doc:
        update_doc["price"] = float(update_doc["price"])
    update_doc["updated_at"] = datetime.utcnow()
    result = await mongo_conn.menu_items.update_one({"_id": oid, "restaurant_id": restaurant_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise ValueError("Menu item not found")
    await mongo_conn.audit_logs.insert_one({
        "actor_email": actor_email,
        "action": "update_menu_item",
        "resource_type": "menu_item",
        "resource_id": item_id,
        "after": update_doc,
        "timestamp": datetime.utcnow()
    })
    return await get_menu_item(restaurant_id, item_id)

async def delete_menu_item(restaurant_id: str, item_id: str, actor_email: str = None):
    try:
        oid = ObjectId(item_id)
    except Exception:
        raise ValueError("Invalid item id")
    result = await mongo_conn.menu_items.delete_one({"_id": oid, "restaurant_id": restaurant_id})
    if result.deleted_count == 0:
        raise ValueError("Menu item not found")
    await mongo_conn.audit_logs.insert_one({
        "actor_email": actor_email,
        "action": "delete_menu_item",
        "resource_type": "menu_item",
        "resource_id": item_id,
        "timestamp": datetime.utcnow()
    })
    logger.info("Menu item deleted", extra={"actor": actor_email, "item_id": item_id})
    return {"message": "deleted", "item_id": item_id}
