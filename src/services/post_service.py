from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from core.database import db
from models.post import Post
from models.user import User
from schemas.post import PostCreate, PostFilters, PostUpdate
from services.utility import generate_slug, verify_unique_slug


class PostService:
    def __init__(self):
        self.database = db.database
        self.posts = self.database.posts
        self.users = self.database.users

    async def create_post(self, post_data: PostCreate, author: User) -> Post:
        post_collection = self.posts
        user_collection = self.users

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
        collection = self.posts

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

    async def update_post(self, post_slug: str, update_data: PostUpdate, user: User):
        collection = self.posts
        data = update_data.model_dump()
        fields = ["title", "content", "tags", "featured_image", "status"]
        to_update = {}

        authorize = user.can_create_posts()
        if not authorize:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You dont have Permissions",
            )
        else:
            post_exists = await collection.find_one({"slug": post_slug})
            if post_exists:
                if user.role == "admin" or (
                    user.role == "author"
                    and user.username == post_exists["author_username"]
                ):
                    if "title" in data.keys():
                        new_slug = verify_unique_slug(generate_slug(text=data["title"]))

                        for field in fields:
                            if data[field] is not None:
                                to_update.update({field: data[field]})

                        to_update.update(
                            {"updated_at": datetime.now(timezone.utc), "slug": new_slug}
                        )

                        await collection.update_one(
                            {"slug": post_slug}, {"$set": to_update}
                        )
                        updated_post = await collection.find_one({"slug": new_slug})

                        return updated_post
                    else:
                        for field in fields:
                            if data[field] is not None:
                                to_update.update({field: data[field]})

                        to_update.update({"updated_at": datetime.now(timezone.utc)})

                        await collection.update_one(
                            {"slug": post_slug}, {"$set": to_update}
                        )
                        updated_post = await collection.find_one({"slug": post_slug})
                        return updated_post
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You dont have Permissions",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
                )

    async def delete_post(self, post_slug: str, user: User) -> bool:
        posts_collection = self.posts
        user_collection = self.users

        post_exists = await posts_collection.find_one({"slug": post_slug})
        if not post_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
            )

        else:
            user_is_reader = user.can_create_posts()
            if user_is_reader:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You dont have Permissions",
                )

            else:
                if (
                    user.role == "author"
                    and post_exists["author_username"] == user.username
                ) or user.role == "admin":
                    await user_collection.update_one(
                        {"username": post_exists["author_username"]},
                        {
                            "$set": {
                                "posts_count": -1,
                                "updated_at": datetime.now(timezone.utc),
                            }
                        },
                    )

                    deleted_post = await posts_collection.delete_one(
                        {"slug": post_slug}
                    )

                    if deleted_post.deleted_count >= 1:
                        return True
                    else:
                        return False
