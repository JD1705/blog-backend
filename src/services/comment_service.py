from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from pymongo import DESCENDING, ReturnDocument

from bson import ObjectId
from core.database import db
from models.comment import Comment
from schemas.comment import CommentCreate, CommentFilters, CommentUpdate
from models.post import Post
from models.user import User


class CommentService:
    def __init__(self):
        self.database = db.database
        self.comments = self.database.comments
        self.users = self.database.users
        self.posts = self.database.posts

    async def create_post_comment(
        self, comment: CommentCreate, user: dict, slug: str
    ) -> Comment:
        post_collection = self.posts
        comment_collection = self.comments

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You dont have Permissions to comment",
            )
        else:
            current_user = User.from_mongo_dict(user)
            post_exists = await post_collection.find_one({"slug": slug})
            if not post_exists or post_exists["status"] != "published":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Post Not found"
                )

            else:
                if comment.parent_id is not None:
                    parent_exists = await comment_collection.find_one(
                        {"_id": ObjectId(comment.parent_id)}
                    )
                    if not parent_exists:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This comment doesnt exists",
                        )
                    else:
                        await comment_collection.update_one(
                            {"_id": ObjectId(comment.parent_id)},
                            {
                                "$set": {
                                    "replies_count": parent_exists["replies_count"] + 1
                                }
                            },
                        )

                comment_for_db = Comment(
                    **comment.model_dump(),
                    post_id=str(post_exists["_id"]),
                    author_id=str(current_user.id),
                    author_username=current_user.username,
                )

                await comment_collection.insert_one(comment_for_db.to_mongo_dict())
                await post_collection.update_one(
                    {"slug": slug},
                    {"$set": {"comments_count": post_exists["comments_count"] + 1}},
                )
                return comment_for_db

    async def get_comments(
        self, slug: str, sort_by: str, limit: int, offset: int, current_user: Optional[User]
    ):
        post = await self.posts.find_one({"slug": slug})

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post Not found"
            )

        query = {"post_id": post["_id"]}

        if sort_by == "newest":
            sort = [("created_at", -1)]
        elif sort_by == "oldest":
            sort = [("created_at", 1)]

        cursor = (
            await self.comments.find(query)
            .sort(sort)
            .limit(limit)
            .skip(offset)
            .to_list()
        )

        comments = []
        for doc in cursor:
            comments.append(Comment.from_mongo_dict(doc))

        total = await self.comments.count_documents(query)
        metadata = {
            "total": total,
            "returned": len(comments),
            "sort": sort_by,
            "has_more": (offset + len(comments)) < total
        }

        return comments, metadata
