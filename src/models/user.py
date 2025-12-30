from datetime import datetime, timezone
from typing import List, Optional

from pydantic import Field
from pymongo import ASCENDING, IndexModel

from .base import MongoModel, PyObjectId


# Modelo principal del Usuario
class User(MongoModel):
    # Campo ID - usa nuestro ObjectId personalizado
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Campos básicos de autenticación (de tus schemas)
    username: str
    email: str
    hashed_password: str

    # Campos específicos del blog
    bio: Optional[str] = None
    role: str = "reader"  # reader, author, admin
    posts_count: int = 0
    is_active: bool = True

    # Timestamps automáticos
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Método para actualizar el timestamp cuando se modifica el usuario
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    # Método para incrementar el contador de posts
    def increment_posts_count(self) -> None:
        self.posts_count += 1
        self.update_timestamp()

    # Método para decrementar el contador de posts
    def decrement_posts_count(self) -> None:
        if self.posts_count > 0:
            self.posts_count -= 1
            self.update_timestamp()

    # Método para verificar si el usuario puede crear posts
    def can_create_posts(self) -> bool:
        return self.role in ["author", "admin"] and self.is_active

    # Método para convertir a diccionario (útil para MongoDB)
    def to_mongo_dict(self) -> dict:
        mongo_dict = self.model_dump(by_alias=True, exclude={"id"})
        if "_id" not in mongo_dict:
            mongo_dict["_id"] = self.id
            return mongo_dict

    # Métodos estáticos (de clase) para operaciones de base de datos
    @classmethod
    def from_mongo_dict(cls, data: dict) -> "User":
        """Crea una instancia User desde un documento de MongoDB"""
        if "_id" in data.keys():
            data["_id"] = str(data["_id"])
            return cls(**data)

    @classmethod
    def get_indexes(cls) -> List[IndexModel]:
        """Índices específicos para la colección de usuarios"""
        return [
            # Índice único para email
            IndexModel([("email", ASCENDING)], unique=True, name="unique_email"),
            # Índice para búsquedas por rol
            IndexModel([("role", ASCENDING)], name="idx_role"),
            # Índice compuesto para búsquedas comunes
            IndexModel(
                [("is_active", ASCENDING), ("created_at", ASCENDING)],
                name="idx_active_created",
            ),
        ]

    @classmethod
    def get_collection_name(cls) -> str:
        """Sobreescribir si necesitas nombre diferente"""
        return "users"
