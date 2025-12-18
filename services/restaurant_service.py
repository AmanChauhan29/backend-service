# services/restaurant_service.py
from db.db_operation import mongo_conn
from datetime import datetime
from bson import ObjectId
from utils.logger import get_logger
from pymongo.errors import PyMongoError
import re

logger = get_logger("Restaurant_Service")

def slugify(name: str) -> str:
    # simple slugify: lower, non-alphanum -> -, remove duplicates
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:100]

async def create_restaurant(payload, actor_email: str = None, approve: bool = False):
    """
    Create a restaurant document. If approve=True or actor is superadmin, mark approved.
    actor_email used for audit.
    """
    restaurants = mongo_conn.restaurants_collection
    existing = await restaurants.find_one({"owner_email": payload.owner_email})
    if existing is not None:
        # handle conflict / owner already has a restaurant
        raise ValueError("Restaurant for this owner already exists")
    slug = slugify(payload.name)
    slug_existing = await restaurants.find_one({"slug": slug})
    if slug_existing is not None:
        raise ValueError("Restaurant with similar name exists, choose a different name")
    now = datetime.utcnow()
    doc = {
        "name": payload.name,
        "description": payload.description,
        "address": payload.address,
        "phone": payload.phone,
        "slug": slug,
        "owner_email": payload.owner_email or None,
        "approved": bool(approve),
        "disabled": False,
        "created_at": now,
        "updated_at": now
    }
    try:
        result = await restaurants.insert_one(doc)
    except PyMongoError:
        logger.exception("DB error creating restaurant")
        raise
    logger.info("Restaurant created", extra={"actor": actor_email, "restaurant_id": str(result.inserted_id)})
    return {
        "id": str(result.inserted_id),
        **{k: doc[k] for k in ("name","description","address","phone","slug","owner_email","approved","disabled")},
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat()
    }

async def get_restaurant_by_id(restaurant_id: str):
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        return None
    restaurants = mongo_conn.restaurants_collection
    doc = await restaurants.find_one({"_id": oid})
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "description": doc.get("description"),
        "address": doc.get("address"),
        "phone": doc.get("phone"),
        "slug": doc.get("slug"),
        "owner_email": doc.get("owner_email"),
        "approved": doc.get("approved", False),
        "disabled": doc.get("disabled", False),
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "updated_at": doc.get("updated_at").isoformat() if doc.get("updated_at") else None
    }

async def list_restaurants(filter_approved: bool | None = None, skip: int = 0, limit: int = 50):
    q = {}
    if filter_approved is True:
        q["approved"] = True
    elif filter_approved is False:
        q["approved"] = False
    cursor = mongo_conn.restaurants_collection.find(q).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    out = []
    for d in docs:
        out.append({
            "id": str(d["_id"]),
            "name": d["name"],
            "description": d.get("description"),
            "address": d.get("address"),
            "phone": d.get("phone"),
            "slug": d.get("slug"),
            "owner_email": d.get("owner_email"),
            "approved": d.get("approved", False),
            "disabled": d.get("disabled", False),
            "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
            "updated_at": d.get("updated_at").isoformat() if d.get("updated_at") else None
        })
    return out

async def update_restaurant(restaurant_id: str, payload, actor_email: str = None):
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise ValueError("Invalid restaurant id")
    update_doc = {k: v for k, v in payload.model_dump().items() if v is not None}
    update_doc["updated_at"] = datetime.utcnow()
    result = await mongo_conn.restaurants_collection.update_one({"_id": oid}, {"$set": update_doc})
    if result.matched_count == 0:
        raise ValueError("Restaurant not found")
    # audit (simple)
    await mongo_conn.audit_logs.insert_one({
        "actor_email": actor_email,
        "action": "update_restaurant",
        "resource_type": "restaurant",
        "resource_id": restaurant_id,
        "after": update_doc,
        "timestamp": datetime.utcnow()
    })
    return await get_restaurant_by_id(restaurant_id)

async def soft_delete_restaurant(restaurant_id: str, actor_email: str = None):
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise ValueError("Invalid restaurant id")
    result = await mongo_conn.restaurants_collection.update_one({"_id": oid}, {"$set": {"disabled": True, "updated_at": datetime.utcnow()}})
    if result.matched_count == 0:
        raise ValueError("Restaurant not found")
    await mongo_conn.audit_logs.insert_one({
        "actor_email": actor_email,
        "action": "disable_restaurant",
        "resource_type": "restaurant",
        "resource_id": restaurant_id,
        "timestamp": datetime.utcnow()
    })
    return {"message": "restaurant_disabled", "restaurant_id": restaurant_id}
