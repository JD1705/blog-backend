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

    async def get_post_by_slug(
        self, slug: str, current_user: Optional[dict] = None
    ) -> Optional[Post]:
        collection = self.database.get_collection("posts")

        response = await collection.find_one({"slug": slug})
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
            )

        if response["status"] != "published" and current_user is not None:  # type: ignore
            if current_user["role"] in ["admin", "author"]:
                post = Post(
                    title=response["title"],
                    content=response["content"],
                    author_id=str(response["author_id"]),
                    tags=response["tags"],
                    featured_image=response["featured_image"],
                    _id=str(response["_id"]),
                    slug=response["slug"],
                    author_username=response["author_username"],
                    status=response["status"],
                    view_count=response["view_count"],
                    comments_count=response["comments_count"],
                    created_at=response["created_at"],
                    updated_at=response["updated_at"],
                    published_at=response["published_at"],
                )
                return post
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
                )

        post = Post(
            title=response["title"],
            content=response["content"],
            author_id=str(response["author_id"]),
            tags=response["tags"],
            featured_image=response["featured_image"],
            _id=str(response["_id"]),
            slug=response["slug"],
            author_username=response["author_username"],
            status=response["status"],
            view_count=response["view_count"],
            comments_count=response["comments_count"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            published_at=response["published_at"],
        )
        return post
