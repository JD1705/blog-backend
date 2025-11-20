from core.database import db
from models.user import User
from schemas.user import UserCreate, UserLogin
from core.security import create_jwt_token, hash_password, verify_password
from fastapi import HTTPException, status


class AuthService:
    def __init__(self):
        self.database = db

    async def register_user(self, user_data: UserCreate) -> User:  # type: ignore
        collection = self.database.database.get_collection("users")  # type: ignore

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
                hashed_password=str(hashed_pwd),
                email=normalized_email,
                bio=user_data.bio,
            )

            await collection.insert_one(new_user.to_mongo_dict())
            return new_user

    async def login_user(self, user_data: UserLogin) -> dict:
        collection = self.database.database.get_collection("users")  # type: ignore
        normalized_email = user_data.email.lower().strip()

        exist_user = await collection.find_one({"email": normalized_email})
        if not exist_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Credentials"
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
