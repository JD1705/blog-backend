from core.database import db
from models.user import User
from schemas.user import UserCreate
from core.security import hash_password
from fastapi import HTTPException, status

class AuthService:
    def __init__(self):
        self.database = db

    async def register_user(self, user_data: UserCreate) -> User: # type: ignore
        collection = self.database.database.get_collection("users") # type: ignore

        hashed_pwd = hash_password(user_data.password)

        normalized_email = user_data.email.lower().strip()
        exist_user = await collection.find_one({"email":normalized_email})
        if exist_user:
            raise HTTPException(
                    detail="User Already Exist",
                    status_code=status.HTTP_409_CONFLICT
                    )

        else:
            new_user = User(
                    username=user_data.username,
                    hashed_password=str(hashed_pwd),
                    email=normalized_email,
                    bio=user_data.bio
                    )
        
            await collection.insert_one(new_user.to_mongo_dict())
            return new_user

