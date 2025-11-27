from core.database import db
from models.user import User
from schemas.user import UserResponse, UserUpdate
from core.security import create_jwt_token, hash_password, verify_password
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from models.token import TokenBlacklist

class UserService:
    def __init__(self):
        self.database = db.database

    async def get_user_profile(self, current_user: dict):
        user_data = UserResponse(
                id=str(current_user["_id"]),
                username=current_user["username"],
                bio=current_user["bio"],
                email=current_user["email"],
                role=current_user["role"],
                post_count=current_user["posts_count"],
                created_at=current_user["created_at"]
                )

        return user_data
