from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    validator,
    model_validator,
    model_serializer,
)
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    @model_validator(mode="before")
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        if isinstance(v, ObjectId):
            return cls(str(v))
        if isinstance(v, str) and ObjectId.is_valid(v):
            return cls(v)
        raise TypeError(f"Invalid type for ObjectId: {type(v)}")

    @classmethod
    @model_serializer
    def serialize(cls, v):
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}


class UserRegister(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128)

    @validator("name")
    def validate_name(cls, v):
        if not v.replace(" ", "").isalpha():
            raise ValueError("Name must contain only alphabetic characters and spaces")
        return v


class UserRead(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: EmailStr

    class Config:
        populate_by_name = True
