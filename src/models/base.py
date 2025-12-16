from typing import Any, List

from bson import ObjectId
from pydantic import BaseModel, GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from pymongo import IndexModel


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> CoreSchema:
        """
        Define how Pydantic should validate and serialize this type.
        it is used internally to build the validation schema.
        """
        return core_schema.chain_schema(
            [
                core_schema.str_schema(),  # first validate that is a string
                core_schema.no_info_plain_validator_function(
                    cls.validate
                ),  # then validate the objectid
            ]
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        """
        Customize how is generated the JSON schema for this type.
        make sure that in the OpenAPI documentation (Swagger) is showed like a 'string'.
        """
        # Get the basic JSON schema from the handler
        json_schema = handler(_core_schema)
        # Make sure that the schema define the type as 'string'
        json_schema.update(type="string", format="objectid")
        return json_schema


class MongoModel(BaseModel):
    @classmethod
    def get_indexes(cls) -> List[IndexModel]:
        """
        Retorna lista de índices para esta colección.
        Sobreescribir en cada modelo hijo.
        """
        return []

    @classmethod
    def get_collection_name(cls) -> str:
        """
        Retorna el nombre de la colección basado en el nombre de la clase.
        User -> "users", Post -> "posts", etc.
        """
        # Convierte "User" a "users", "Post" to "posts"
        return cls.__name__.lower() + "s"

    class Config:
        validate_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
