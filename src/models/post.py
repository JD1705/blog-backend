from datetime import datetime, timezone
from typing import List, Optional

from pydantic import Field, field_validator
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel

from .base import MongoModel, PyObjectId


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

    # Método para convertir a diccionario (útil para MongoDB)
    def to_mongo_dict(self) -> dict:
        mongo_dict = self.model_dump(by_alias=True, exclude={"id"})
        if "_id" not in mongo_dict:
            mongo_dict["_id"] = self.id
            return mongo_dict

    # Métodos estáticos (de clase) para operaciones de base de datos
    @classmethod
    def from_mongo_dict(cls, data: dict) -> "Post":
        """Crea una instancia User desde un documento de MongoDB"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
            data["author_id"] = str(data["author_id"])
            return cls(**data)

    @classmethod
    def get_indexes(cls) -> List[IndexModel]:
        """Índices para la colección de posts"""
        return [
            # 1. Slug único
            IndexModel([("slug", ASCENDING)], unique=True, name="unique_slug"),
            # 2. Autor + fecha creación
            IndexModel(
                [("author_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_author_created",
            ),
            # 3. Estado + fecha publicación
            IndexModel(
                [("status", ASCENDING), ("published_at", DESCENDING)],
                partialFilterExpression={"status": "published"},
                name="idx_status_published",
            ),
            # 4. Tags
            IndexModel([("tags", ASCENDING)], name="idx_tags"),
            # 5. Búsqueda full-text
            IndexModel(
                [("title", TEXT), ("content", TEXT)],
                default_language="spanish",
                name="text_search",
            ),
            # 6. Vistas populares
            IndexModel([("view_count", DESCENDING)], name="idx_popular"),
            # 7. Comentarios (para posts más comentados)
            IndexModel([("comments_count", DESCENDING)], name="idx_commented"),
            # 8. Índice compuesto para listados comunes
            IndexModel(
                [
                    ("status", ASCENDING),
                    ("published_at", DESCENDING),
                    ("view_count", DESCENDING),
                ],
                name="idx_frontpage",
            ),
        ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "posts"
