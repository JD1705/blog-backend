from pydantic import (
    BaseModel,
    Field,
    field_validator,
    EmailStr,
    SecretStr,
)
from typing import Optional
from datetime import datetime, timezone


class UserCreate(BaseModel):
    username: str
    bio: str | None = None
    email: EmailStr
    password: SecretStr
    confirm_password: SecretStr

    @field_validator("confirm_password")
    def validate_passwords(cls, v, values):
        if "password" in values.data and v != values.data["password"]:
            raise ValueError("Passwords dont match")
        return v


class UserResponse(BaseModel):
    id: str
    username: str
    bio: str | None = None
    email: EmailStr
    role: str
    post_count: int = 0
    is_active: bool = True
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = (
        None  # EmailStr validates automatically that the email is not ""
    )
    bio: Optional[str] = None


class UserPublic(BaseModel):
    id: str
    username: str
    role: str

