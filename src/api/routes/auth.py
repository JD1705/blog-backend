from services.auth_services import AuthService
from schemas.user import UserCreate, UserResponse, UserLogin
from fastapi import APIRouter, status, Depends, HTTPException
from api.dependencies import get_token

router = APIRouter(prefix="/auth")


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, auth_service: AuthService = Depends()):
    user = await auth_service.register_user(user_data)

    response = UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        bio=user.bio,
        created_at=user.created_at,
        role=user.role,
    )

    return response


@router.post("/login")
async def login(user_data: UserLogin, auth_service: AuthService = Depends()):
    response = await auth_service.login_user(user_data)

    return response


@router.post("/logout")
async def logout(
    token: str = Depends(get_token), auth_service: AuthService = Depends()
):
    token_in_blacklist = await auth_service.is_blacklisted_token(token)
    if token_in_blacklist == False:
        success = await auth_service.logout_user(token)

        if success:
            return {"message": "Logout Successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="logout failed"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authenticated"
        )
