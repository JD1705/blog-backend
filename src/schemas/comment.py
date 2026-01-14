from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[str] = None

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_id: str
    author_username: str
    parent_id: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    replies_count: int = Field(default=0, ge=0)

class CommentFilters(BaseModel):
    post_id: Optional[str] = None
    author_id: Optional[str] = None
    parent_id: Optional[str] = None
    include_deleted: bool = False
