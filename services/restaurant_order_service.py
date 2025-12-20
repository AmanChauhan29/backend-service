from db.db_operation import mongo_conn

async def fetch_orders_for_restaurant_admin(restaurant_ids: list):
    orders_collection = mongo_conn.orders_collection
    cursor = orders_collection.find({
        "restaurant_id": {"$in": restaurant_ids}
    })
    orders = await cursor.to_list(length=None)
    return orders