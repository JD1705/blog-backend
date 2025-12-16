from datetime import datetime
from pydantic import Field
from bson import ObjectId
from models.base import PyObjectId, MongoModel
from pymongo import ASCENDING, IndexModel
from typing import List


class TokenBlacklist(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    token: str
    expires_at: datetime

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    # Método para convertir a diccionario (útil para MongoDB)
    def to_mongo_dict(self) -> dict:
        mongo_dict = self.model_dump(by_alias=True, exclude={"id"})
        if "_id" not in mongo_dict:
            mongo_dict["_id"] = self.id
        return mongo_dict

    # Métodos estáticos (de clase) para operaciones de base de datos
    @classmethod
    def from_mongo_dict(cls, data: dict) -> "TokenBlacklist":
        """Crea una instancia User desde un documento de MongoDB"""
        if "_id" in data:
            data["id"] = str(data["_id"])
        return cls(**data)

    @classmethod
    def get_indexes(cls) -> List[IndexModel]:
        return [
            # Índice TTL para expiración automática
            IndexModel(
                [("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expires"
            ),
            # Índice para búsqueda rápida por token
            IndexModel([("token", ASCENDING)], name="idx_token"),
            # Índice para usuario + token
            IndexModel(
                [("user_id", ASCENDING), ("token", ASCENDING)], name="idx_user_token"
            ),
        ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "token_blacklist"
