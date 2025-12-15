from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from core.database import db
from models.post import Post
from models.user import User
from schemas.post import PostCreate, PostFilters, PostUpdate
from services.utility import generate_slug


class PostService:
    def __init__(self):
        self.database = db.database

    async def create_post(self, post_data: PostCreate, author: User) -> Post:
        post_collection = self.database.get_collection("posts")
        user_collection = self.database.get_collection("users")

        if not author.can_create_posts():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="")

        slug = generate_slug(text=post_data.title)
        created_post = Post(
            **post_data.model_dump(),
            slug=slug,
            author_username=author.username,
            author_id=str(author.id),
        )
        await post_collection.insert_one(created_post.model_dump())

        author.increment_posts_count()
        await user_collection.update_one(
            {"_id": author.id},
            {
                "$set": {
                    "posts_count": author.posts_count,
                    "updated_at": author.updated_at,
                }
            },
        )

        return created_post
