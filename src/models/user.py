from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# Modelo principal del Usuario
class User(BaseModel):
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
    created_at: datetime = Field(default=datetime.now(timezone.utc))  # type: ignore
    updated_at: datetime = Field(default=datetime.now(timezone.utc))  # type: ignore

    # Configuración de Pydantic para este modelo
    class Config:
        validate_by_name = True  # Permite usar alias o nombre real
        arbitrary_types_allowed = True  # Permite tipos personalizados como PyObjectId
        json_encoders = {ObjectId: str}  # Convierte ObjectId a string en JSON
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "bio": "A passionate blogger",
                "role": "author",
                "posts_count": 5,
            }
        }

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
        if "_id" in data:
            data["id"] = str(data["_id"])
        return cls(**data)

