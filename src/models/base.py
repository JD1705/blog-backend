from pydantic import BaseModel, GetJsonSchemaHandler
from bson import ObjectId
from typing import Any
from pydantic_core import CoreSchema, core_schema


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
    class Config:
        validate_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
