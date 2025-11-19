from services.auth_services import AuthService
from schemas.user import UserCreate, UserResponse
from fastapi import APIRouter, status, Depends

router = APIRouter(prefix="/auth")

@router.post("/register",response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, auth_service: AuthService = Depends()):
    user = await auth_service.register_user(user_data)

    response = UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            bio=user.bio,
            created_at=user.created_at,
            role=user.role
            )

    return response
