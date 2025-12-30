from core.database import db
from models.user import User
from schemas.user import UserCreate, UserLogin
from core.security import create_jwt_token, hash_password, verify_password
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from models.token import TokenBlacklist


class AuthService:
    def __init__(self):
        self.database = db
        self.users = self.database.users

    async def register_user(self, user_data: UserCreate) -> User:  # type: ignore
        collection = self.users

        hashed_pwd = hash_password(user_data.password)

        normalized_email = user_data.email.lower().strip()
        exist_user = await collection.find_one({"email": normalized_email})
        if exist_user:
            raise HTTPException(
                detail="User Already Exist", status_code=status.HTTP_409_CONFLICT
            )

        else:
            new_user = User(
                username=user_data.username,
                hashed_password=hashed_pwd,
                email=normalized_email,
                bio=user_data.bio,
            )

            await collection.insert_one(new_user.to_mongo_dict())
            return new_user

    async def login_user(self, user_data: UserLogin) -> dict:
        collection = self.users
        normalized_email = user_data.email.lower().strip()

        exist_user = await collection.find_one({"email": normalized_email})
        if not exist_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Credentials"
            )

        elif not exist_user["is_active"] == True:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
            )

        else:
            verify = verify_password(user_data.password, exist_user["hashed_password"])
            if verify:
                access_token = create_jwt_token({"sub": str(exist_user["_id"])})

                return {"access_token": access_token, "token_type": "bearer"}

            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect Credentials",
                )

    async def logout_user(self, token: str, expires_time: int = 24) -> bool:
        collection = self.database.token_blacklist
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_time)

        blacklisted_token = TokenBlacklist(token=token, expires_at=expires_at)

        await collection.insert_one(blacklisted_token.to_mongo_dict())
        return True

    async def is_blacklisted_token(self, token: str) -> bool:
        collection = self.database.token_blacklist

        result = await collection.find_one({"token": token})
        if result is not None:
            return True
        else:
            return False
