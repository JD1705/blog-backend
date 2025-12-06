from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class PostBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=5)
    tags: List[str] = Field(default_factory=list, max_length=10)
    featured_image: Optional[str] = None

    @field_validator("tags")
    def normalize_tags(cls, v: List[str]):
        normalized_tags = []
        for i in v:
            normalized_tags.append(i.strip().lower().replace(" ", "-"))
        return normalized_tags

class PostCreate(PostBase):
    status: PostStatus = PostStatus.DRAFT

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    content: Optional[str] = Field(None, min_length=5)
    tags: Optional[List[str]] = Field(None, max_length=10)
    featured_image: Optional[str] = None
    status: Optional[PostStatus] = None

    @field_validator("tags")
    def normalize_tags(cls, v: List[str]):
        normalized_tags = []
        for i in v:
            normalized_tags.append(i.strip().lower().replace(" ", "-"))

        return normalized_tags

class PostResponse(PostBase):
    id: str  
    slug: str  
    author_id: str  
    author_username: str  
    status: PostStatus
    view_count: int = 0
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
class PostListResponse(BaseModel):
    id: str
    title: str
    slug: str
    author_username: str
    excerpt: str  # First 150 chars from the content
    tags: List[str]
    featured_image: Optional[str]
    view_count: int
    comments_count: int
    created_at: datetime
    published_at: Optional[datetime]
    status: PostStatus
    
class PostFilters(BaseModel):
    status: Optional[PostStatus] = PostStatus.PUBLISHED
    author_username: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None  # search in títle and content
    min_views: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    class Config:
        extra = "forbid"  # forbid additional fields
