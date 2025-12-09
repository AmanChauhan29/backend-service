# services/admin_service.py
from db.db_operation import mongo_conn
from datetime import datetime
from utils.logger import get_logger
from bson import ObjectId
from pymongo.errors import PyMongoError

logger = get_logger("Admin_Service")

async def promote_user_to_restaurant_admin(target_email: str, restaurant_ids: list, actor_email: str):
    """
    Promote an existing user to restaurant_admin and assign restaurant_ids.
    Also increments token_version to revoke existing tokens.
    actor_email: email of the admin who performed this action (for audit log).
    """
    users_col = mongo_conn.users_collection
    # Find user
    user = await users_col.find_one({"email": target_email})
    if not user:
        raise ValueError("User not found")

    # Update role, restaurant_ids and bump token_version
    result = await users_col.update_one(
        {"email": target_email},
        {
            "$set": {
                "role": "restaurant_admin",
                "restaurant_ids": restaurant_ids,
                "updated_at": datetime.utcnow()
            },
            "$inc": {"token_version": 1}
        }
    )

    # Simple check
    if result.matched_count == 0:
        raise ValueError("Failed to update user")

    # Write audit log
    audit = {
        "actor": actor_email,
        "action": "promote_user",
        "target": target_email,
        "role": "restaurant_admin",
        "restaurant_ids": restaurant_ids,
        "timestamp": datetime.utcnow()
    }
    await mongo_conn.audit_logs.insert_one(audit)

    logger.info(f"{actor_email} promoted {target_email} to restaurant_admin for restaurants {restaurant_ids}")
    return {"message": "User promoted", "email": target_email, "role": "restaurant_admin", "restaurant_ids": restaurant_ids}

#admin can list users with pagination
async def list_users(skip: int = 0, limit: int = 50):
    """
    Return list of users with pagination.
    """
    users_col = mongo_conn.users_collection
    cursor = users_col.find({}, {"password": 0}).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    # map to API-friendly dicts
    return [
        {
            "id": str(u["_id"]),
            "email": u["email"],
            "full_name": u.get("full_name"),
            "role": u.get("role", "user"),
            "restaurant_ids": u.get("restaurant_ids", []),
            "disabled": u.get("disabled", False)
        } for u in users
    ]

#admin can get user details using user id 
async def get_user_by_id(user_id: str):
    """
    Fetch a single user by id.
    """
    users_col = mongo_conn.users_collection
    user = await users_col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        return None
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user.get("full_name"),
        "role": user.get("role", "user"),
        "restaurant_ids": user.get("restaurant_ids", []),
        "token_version": int(user.get("token_version", 0)),
        "disabled": user.get("disabled", False),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at")
    }

async def change_user_role(target_user_id: str, new_role: str, restaurant_ids: list, actor_email: str, reason: str | None = None):
    """
    Atomically change user's role and restaurant_ids, increment token_version,
    and insert an audit log. Uses transaction when possible.
    """
    users_col = mongo_conn.users_collection
    audit_col = mongo_conn.audit_logs

    # Build before snapshot for audit
    before_doc = await users_col.find_one({"_id": ObjectId(target_user_id)}, {"password": 0})
    if not before_doc:
        raise ValueError("User not found")

    before_snapshot = {
        "role": before_doc.get("role"),
        "restaurant_ids": before_doc.get("restaurant_ids")
    }

    after_snapshot = {
        "role": new_role,
        "restaurant_ids": restaurant_ids
    }

    audit_doc = {
        "actor_email": actor_email,
        "action": "change_role",
        "resource_type": "user",
        "resource_id": target_user_id,
        "before": before_snapshot,
        "after": after_snapshot,
        "reason": reason,
        "timestamp": datetime.utcnow()
    }

    # Try to use transactions if client is available
    client = getattr(mongo_conn, "client", None)
    try:
        if client is not None:
            # Motor client supports start_session for transactions
            async with client.start_session() as session:
                async with session.start_transaction():
                    result = await users_col.update_one(
                        {"_id": ObjectId(target_user_id)},
                        {
                            "$set": {
                                "role": new_role,
                                "restaurant_ids": restaurant_ids,
                                "updated_at": datetime.utcnow()
                            },
                            "$inc": {"token_version": 1}
                        },
                        session=session
                    )
                    if result.matched_count == 0:
                        raise ValueError("User not found during update")

                    await audit_col.insert_one(audit_doc, session=session)
        else:
            # fallback without transaction
            result = await users_col.update_one(
                {"_id": ObjectId(target_user_id)},
                {
                    "$set": {
                        "role": new_role,
                        "restaurant_ids": restaurant_ids,
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"token_version": 1}
                }
            )
            if result.matched_count == 0:
                raise ValueError("User not found during update")
            await audit_col.insert_one(audit_doc)
    except PyMongoError as e:
        logger.exception("DB error while changing role")
        raise

    logger.info(f"{actor_email} changed role of {target_user_id} -> {new_role}")
    return {"message": "role_changed", "user_id": target_user_id, "role": new_role, "restaurant_ids": restaurant_ids}

async def revoke_user_tokens(target_user_id: str, actor_email: str, reason: str | None = None):
    """
    Increment token_version to revoke tokens and create audit log.
    """
    users_col = mongo_conn.users_collection
    audit_col = mongo_conn.audit_logs

    user = await users_col.find_one({"_id": ObjectId(target_user_id)}, {"password": 0})
    if not user:
        raise ValueError("User not found")

    audit_doc = {
        "actor_email": actor_email,
        "action": "revoke_tokens",
        "resource_type": "user",
        "resource_id": target_user_id,
        "before": {"token_version": int(user.get("token_version", 0))},
        "after": {"token_version": int(user.get("token_version", 0)) + 1},
        "reason": reason,
        "timestamp": datetime.utcnow()
    }

    result = await users_col.update_one({"_id": ObjectId(target_user_id)}, {"$inc": {"token_version": 1}})
    if result.matched_count == 0:
        raise ValueError("User not found during revoke")

    await audit_col.insert_one(audit_doc)
    logger.info(f"{actor_email} revoked tokens for {target_user_id}")
    return {"message": "tokens_revoked", "user_id": target_user_id}

async def disable_user(target_user_id: str, actor_email: str, reason: str | None = None):
    """
    Soft-disable a user account (set disabled=true) and bump token_version.
    """
    users_col = mongo_conn.users_collection
    audit_col = mongo_conn.audit_logs

    user = await users_col.find_one({"_id": ObjectId(target_user_id)}, {"password": 0})
    if not user:
        raise ValueError("User not found")

    before_snapshot = {"disabled": user.get("disabled", False)}
    after_snapshot = {"disabled": True}

    audit_doc = {
        "actor_email": actor_email,
        "action": "disable_user",
        "resource_type": "user",
        "resource_id": target_user_id,
        "before": before_snapshot,
        "after": after_snapshot,
        "reason": reason,
        "timestamp": datetime.utcnow()
    }

    result = await users_col.update_one({"_id": ObjectId(target_user_id)}, {"$set": {"disabled": True, "updated_at": datetime.utcnow()}, "$inc": {"token_version": 1}})
    if result.matched_count == 0:
        raise ValueError("User not found during disable")

    await audit_col.insert_one(audit_doc)
    logger.info(f"{actor_email} disabled user {target_user_id}")
    return {"message": "user_disabled", "user_id": target_user_id}

async def list_audit_logs(skip: int = 0, limit: int = 50):
    """
    Simple pagination for audit logs, newest first.
    """
    audit_col = mongo_conn.audit_logs
    cursor = audit_col.find({}).sort("timestamp", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    # return shape for API
    return [
        {
            "id": str(a["_id"]),
            "actor_email": a["actor_email"],
            "action": a["action"],
            "resource_type": a["resource_type"],
            "resource_id": a["resource_id"],
            "before": a.get("before"),
            "after": a.get("after"),
            "reason": a.get("reason"),
            "timestamp": a["timestamp"]
        } for a in items
    ]