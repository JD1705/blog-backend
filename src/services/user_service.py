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
            created_at=current_user["created_at"],
        )

        return user_data

    async def update_user_profile(self, current_user: dict, update_data: UserUpdate):
        collection = self.database.get_collection("users")  # type: ignore
        data = update_data.model_dump()
        to_update = {}
        fields = ["email", "username", "bio"]

        if data["email"] is not None:
            normalized_email = update_data.email.lower().strip()  # type: ignore
            user_exists = await collection.find_one({"email": normalized_email})

            if not user_exists:
                for field in fields:
                    if data[field] is not None:
                        to_update.update({field: data[field]})

                to_update.update({"updated_at": datetime.now(timezone.utc)})
                await collection.update_one(
                    {"_id": current_user["_id"]}, {"$set": to_update}
                )
                updated_user = await collection.find_one({"_id": current_user["_id"]})

                return UserResponse(
                    id=str(updated_user["_id"]),  # type: ignore
                    username=updated_user["username"],  # type: ignore
                    bio=updated_user["bio"],  # type: ignore
                    email=updated_user["email"],  # type: ignore
                    role=updated_user["role"],  # type: ignore
                    post_count=updated_user["posts_count"],  # type: ignore
                    created_at=updated_user["created_at"],  # type: ignore
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Incorrect Credentials"
                )

        else:
            for field in fields:
                if data[field] is not None:
                    to_update.update({field: data[field]})

            to_update.update({"updated_at": datetime.now(timezone.utc)})
            await collection.update_one(
                {"_id": current_user["_id"]}, {"$set": to_update}
            )
            updated_user = await collection.find_one({"_id": current_user["_id"]})

            return UserResponse(
                id=str(updated_user["_id"]),  # type: ignore
                username=updated_user["username"],  # type: ignore
                bio=updated_user["bio"],  # type: ignore
                email=updated_user["email"],  # type: ignore
                role=updated_user["role"],  # type: ignore
                post_count=updated_user["posts_count"],  # type: ignore
                created_at=updated_user["created_at"],  # type: ignore
            )

    async def deactivate_user(self, current_user: dict):
        collection = self.database.get_collection("users") # type: ignore
        await collection.update_one({"_id":current_user["_id"]}, {"$set": {"is_active":False}})
