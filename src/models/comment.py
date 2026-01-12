from datetime import datetime, timezone
from typing import List, Optional

from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from .base import MongoModel, PyObjectId

class Comment(MongoModel):
    # Identifier Fields
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    post_id: PyObjectId
    author_id: PyObjectId
    author_username: str
    parent_id: Optional[PyObjectId] = None

    # Content & State
    content: str
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    replies_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Validators
    def is_root(self):
        if self.parent_id is None:
            return True
        else:
            return False

    def to_mongo_dict(self) -> dict:
        mongo_dict = self.model_dump(by_alias=True, exclude={"id"})
        if "_id" not in mongo_dict:
            mongo_dict["_id"] = self.id
            return mongo_dict

    # Static Methods (for class) for database operations
    @classmethod
    def from_mongo_dict(cls, data: dict) -> "Comment":
        """Create a Comment instance from a MongoDB Document"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
            data["author_id"] = str(data["author_id"])
            data["post_id"] = str(data["post_id"])

            if "parent_id" in data is not None:
                data["parent_id"] = str(data["parent_id"])
                return cls(**data)
            return cls(**data)

    @classmethod
    def get_indexes(cls) -> List[IndexModel]:
        """Indexes for comments collection"""
        return [
            IndexModel([("post_id", ASCENDING), ("created_at", DESCENDING)], name="idx_post_created"),
            IndexModel(
                [("post_id", ASCENDING), ("parent_id", ASCENDING)],
                name="idx_post_parent",
                partialFilterExpression={"parent_id":None}
            ),
            IndexModel(
                [("parent_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_parent_created",
            ),
            IndexModel([("author_id", ASCENDING), ("created_at", DESCENDING)], name="idx_author_created"),
            IndexModel(
                [("is_deleted", ASCENDING), ("created_at", DESCENDING)],
                name="idx_deleted_created",
                partialFilterExpression={"is_deleted":True}
            ),
            IndexModel(
                [
                    ("post_id", ASCENDING),
                    ("is_deleted", ASCENDING),
                    ("created_at", DESCENDING),
                ],
                name="idx_post_status_created",
            ),
        ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "comments"
