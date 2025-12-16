from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security import verify_token
from core.database import db
from bson import ObjectId
from services.auth_services import AuthService

security = HTTPBearer(auto_error=False)
auth_service = AuthService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Token: it does not have user_id",
            )

        collection = db.database.get_collection("users")  # type: ignore
        user = await collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
            )

        elif not user["is_active"] == True:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
            )

        is_token_blakclisted = await auth_service.is_blacklisted_token(token)
        if is_token_blakclisted == True:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authenticated",
            )

        return user

    except Exception as e:
        raise e


async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                detail="Invalid Token", status_code=status.HTTP_401_UNAUTHORIZED
            )

        return token
    except Exception as e:
        raise e
