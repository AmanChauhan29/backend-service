# routes/restaurant_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from core.dependencies import get_current_user, require_role, CurrentUser
from models.restaurant import RestaurantCreate, RestaurantOut, RestaurantListItem, RestaurantUpdate
from services.restaurant_service import create_restaurant, get_restaurant_by_id, list_restaurants, update_restaurant, soft_delete_restaurant
from utils.logger import get_logger

logger = get_logger("Restaurant_Route")
router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

# Public: list approved restaurants
@router.get("/", response_model=list[RestaurantListItem])
async def api_list_restaurants(approved: bool | None = Query(True), skip: int = 0, limit: int = 50):
    """
    Public listing. approved=True by default (only show approved restaurants).
    Pass approved=null to list all (for admins).
    """
    # Query param approved can be 'True', 'False', or omitted (None)
    res = await list_restaurants(filter_approved=approved, skip=skip, limit=limit)
    return res

# Public: get single restaurant
@router.get("/{restaurant_id}", response_model=RestaurantOut)
async def api_get_restaurant(restaurant_id: str = Path(...)):
    r = await get_restaurant_by_id(restaurant_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return r

# Superadmin: create restaurant and auto-approve
@router.post("/", response_model=RestaurantOut, dependencies=[Depends(require_role("superadmin"))])
async def api_create_restaurant(payload: RestaurantCreate = Body(...), current_admin: CurrentUser = Depends(get_current_user)):
    try:
        res = await create_restaurant(payload, actor_email=current_admin.email, approve=True)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# Restaurant admin: update own restaurant (needs check)
@router.patch("/{restaurant_id}", response_model=RestaurantOut)
async def api_update_restaurant(restaurant_id: str, payload: RestaurantUpdate = Body(...), current_user: CurrentUser = Depends(get_current_user)):
    # allow only superadmin or restaurant_admin owning this restaurant
    if current_user.role != "superadmin" and (restaurant_id not in current_user.restaurant_ids):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this restaurant")
    try:
        updated = await update_restaurant(restaurant_id, payload, actor_email=current_user.email)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception("Error updating restaurant")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# Superadmin: soft delete
@router.post("/{restaurant_id}/disable", dependencies=[Depends(require_role("superadmin"))])
async def api_disable_restaurant(restaurant_id: str, current_admin: CurrentUser = Depends(get_current_user)):
    try:
        res = await soft_delete_restaurant(restaurant_id, actor_email=current_admin.email)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.exception("Error disabling restaurant")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
