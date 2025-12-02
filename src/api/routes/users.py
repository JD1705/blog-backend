from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import get_current_user
from services.user_service import UserService
from schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users")

@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user), user_service: UserService = Depends()):
    response = await user_service.get_user_profile(current_user)

    return response

@router.put("/me", response_model=UserResponse)
async def update_profile(update_data: UserUpdate, current_user: dict = Depends(get_current_user), user_service: UserService = Depends()):
    response = await user_service.update_user_profile(current_user, update_data)

    return response

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(current_user: dict = Depends(get_current_user), user_service: UserService = Depends()):
    await user_service.deactivate_user(current_user)
