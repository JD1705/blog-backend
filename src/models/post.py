from datetime import datetime, timezone
from typing import List, Optional
from pydantic import Field, field_validator
from .base import PyObjectId, MongoModel


class Post(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    slug: str = Field(..., min_length=3, max_length=200)
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=300)
    tags: List[str] = Field(default_factory=list)
    featured_image: Optional[str] = None

    author_id: PyObjectId = Field(...)
    author_username: str = Field(..., max_length=50)

    status: str = Field(default="draft")
    view_count: int = Field(default=0, ge=0)  # ge=0 -> "greater or equal"
    comments_count: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_statuses = {"draft", "published", "archived"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v
