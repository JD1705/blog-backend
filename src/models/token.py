from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from bson import ObjectId
from models.user import PyObjectId

class TokenBlacklist(BaseModel):
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

