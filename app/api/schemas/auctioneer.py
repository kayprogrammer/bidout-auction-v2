from typing import Optional

from pydantic import BaseModel, validator, Field
from datetime import datetime
from uuid import UUID
from .base import ResponseSchema
from app.db.managers.accounts import user_manager

from app.core.database import SessionLocal

# CREATE LISTING #


class CreateListingSchema(BaseModel):
    name: str = Field(..., max_length=50)
    desc: str
    category_slug: Optional[str]
    price: int
    closing_date: datetime
    file_type: str

    @validator("closing_date")
    def validate_closing_date(cls, v):
        if datetime.utcnow() > v:
            raise ValueError("Closing date must be beyond the current datetime!")
        return v


# ---------------------------------------------------------- #

# USER PROFILE #


class UpdateProfileSchema(BaseModel):
    first_name: str
    last_name: str
    file_type: str


# RESPONSE FOR PUT REQUEST
class UpdateProfileResponseDataSchema(ResponseSchema):
    first_name: str
    last_name: str
    # upload_url: str


class UpdateProfileResponseSchema(ResponseSchema):
    data: UpdateProfileResponseDataSchema


# RESPONSE FOR GET REQUEST
class ProfileDataSchema(BaseModel):
    first_name: str
    last_name: str
    # avatar: str


class ProfileResponseSchema(ResponseSchema):
    data: ProfileDataSchema


# ---------------------------------------- #
