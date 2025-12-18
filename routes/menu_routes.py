from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from models.menu import MenuItemCreate, MenuItemOut, MenuItemUpdate
from services.menu_service import create_menu_item, list_menu_items, get_menu_item, update_menu_item, delete_menu_item
from core.dependencies import get_current_user
from utils.logger import get_logger
from typing import List

logger = get_logger("Menu_Route")
router = APIRouter(prefix="/menu", tags=["Menu"])

# Public: list visible menu items for a restaurant
@router.get("/{restaurant_id}", response_model=List[MenuItemOut])
async def api_list_menu(restaurant_id: str = Path(...), available: bool = Query(True)):
    try:
        items = await list_menu_items(restaurant_id, only_available=available)
        return items
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Error listing menu")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# Restaurant-admin / superadmin: create item
@router.post("/{restaurant_id}", response_model=MenuItemOut)
async def api_create_menu_item(restaurant_id: str, payload: MenuItemCreate = Body(...), current_user = Depends(get_current_user)):
    # RBAC: allow superadmin or restaurant_admin who owns this restaurant
    if current_user.role != "superadmin" and restaurant_id not in current_user.restaurant_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create items for this restaurant")
    try:
        item = await create_menu_item(restaurant_id, payload, actor_email=current_user.email)
        return item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        logger.exception("Error creating menu item")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.patch("/{restaurant_id}/{item_id}", response_model=MenuItemOut)
async def api_update_menu_item(restaurant_id: str, item_id: str, payload: MenuItemUpdate = Body(...), current_user = Depends(get_current_user)):
    if current_user.role != "superadmin" and restaurant_id not in current_user.restaurant_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this item")
    try:
        updated = await update_menu_item(restaurant_id, item_id, payload, actor_email=current_user.email)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.exception("Error updating menu item")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.delete("/{restaurant_id}/{item_id}")
async def api_delete_menu_item(restaurant_id: str, item_id: str, current_user = Depends(get_current_user)):
    if current_user.role != "superadmin" and restaurant_id not in current_user.restaurant_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this item")
    try:
        res = await delete_menu_item(restaurant_id, item_id, actor_email=current_user.email)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.exception("Error deleting menu item")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
