from typing import Optional, Any

from pydantic import BaseModel, validator, Field, StrictStr
from datetime import datetime
from uuid import UUID
from .base import ResponseSchema

from app.api.utils.file_types import ALLOWED_IMAGE_TYPES
from app.api.utils.file_processors import FileProcessor
from pytz import UTC
from decimal import Decimal

# CREATE LISTING #


class CreateListingSchema(BaseModel):
    name: StrictStr = Field(..., example="Product name", max_length=70)
    desc: str = Field(..., example="Product description")
    category: Optional[StrictStr] = Field(..., example="category_slug")
    price: Decimal = Field(..., example=1000.00, decimal_places=2)
    closing_date: datetime
    file_type: str = Field(..., example="image/jpeg")

    @validator("closing_date")
    def validate_closing_date(cls, v):
        if datetime.utcnow().replace(tzinfo=UTC) > v:
            raise ValueError("Closing date must be beyond the current datetime!")
        return v

    @validator("file_type")
    def validate_file_type(cls, v):
        if not v in ALLOWED_IMAGE_TYPES:
            raise ValueError("Image type not allowed!")
        return v

    @validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Must be greater than 0!")
        return v

    class Config:
        error_msg_templates = {
            "value_error.any_str.max_length": "70 characters max!",
        }


class UpdateListingSchema(BaseModel):
    name: Optional[StrictStr] = Field(None, example="Product name", max_length=70)
    desc: Optional[str] = Field(None, example="Product description")
    category: Optional[StrictStr] = Field(None, example="category_slug")
    price: Optional[Decimal] = Field(None, example=1000.00, decimal_places=2)
    closing_date: Optional[datetime]
    active: Optional[bool]
    file_type: Optional[str] = Field(None, example="image/jpeg")

    @validator("closing_date")
    def validate_closing_date(cls, v):
        if datetime.utcnow().replace(tzinfo=UTC) > v:
            raise ValueError("Closing date must be beyond the current datetime!")
        return v

    @validator("file_type")
    def validate_file_type(cls, v):
        if not v in ALLOWED_IMAGE_TYPES:
            raise ValueError("Image type not allowed!")
        return v

    @validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Must be greater than 0!")
        return v

    class Config:
        error_msg_templates = {
            "value_error.any_str.max_length": "70 characters max!",
        }


class CreateListingResponseDataSchema(BaseModel):
    name: str
    auctioneer: dict = Field(
        None, example={"name": "John Doe", "avatar": "https://image.url"}
    )

    slug: str
    desc: str

    category: Optional[str]

    price: Decimal = Field(..., example=1000.00, decimal_places=2)
    closing_date: Any
    active: bool
    bids_count: int
    image_id: UUID = Field(..., example="Ignore this")
    file_upload_data: Optional[dict]

    @validator("file_upload_data", always=True)
    def assemble_file_upload_data(cls, v, values):
        image_id = values.get("image_id")
        if image_id:
            values.pop("image_id", None)
            return FileProcessor.generate_file_signature(
                key=image_id,
                folder="listings",
            )
        values.pop("image_id", None)
        return None

    @validator("auctioneer", pre=True)
    def show_auctioneer(cls, v):
        avatar = None
        if v.avatar_id:
            avatar = FileProcessor.generate_file_url(
                key=v.avatar_id,
                folder="avatars",
                content_type=v.avatar.resource_type,
            )
        return {"name": v.full_name, "avatar": avatar}

    @validator("category", pre=True)
    def show_category(cls, v):
        return v.name if v else "Other"

    class Config:
        orm_mode = True


class CreateListingResponseSchema(ResponseSchema):
    data: CreateListingResponseDataSchema


# ---------------------------------------------------------- #

# USER PROFILE #


class UpdateProfileSchema(BaseModel):
    first_name: str = Field(..., example="John", max_length=50)
    last_name: str = Field(..., example="Doe", max_length=50)
    file_type: Optional[str] = Field(None, example="image/png")

    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.split(" ")) > 1:
            raise ValueError("No spacing allowed")
        return v

    @validator("file_type")
    def validate_file_type(cls, v):
        if v and v not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Image type not allowed!")
        return v

    class Config:
        error_msg_templates = {
            "value_error.any_str.max_length": "50 characters max!",
        }


# RESPONSE FOR PUT REQUEST
class UpdateProfileResponseDataSchema(BaseModel):
    first_name: str
    last_name: str
    avatar_id: UUID = Field(..., example="Ignore this")
    file_upload_data: Optional[dict]

    @validator("file_upload_data", always=True)
    def assemble_file_upload_data(cls, v, values):
        avatar_id = values.get("avatar_id")
        if avatar_id:
            values.pop("avatar_id", None)
            return FileProcessor.generate_file_signature(
                key=avatar_id,
                folder="avatars",
            )
        values.pop("avatar_id", None)
        return None

    class Config:
        orm_mode = True


class UpdateProfileResponseSchema(ResponseSchema):
    data: UpdateProfileResponseDataSchema


# RESPONSE FOR GET REQUEST
class ProfileDataSchema(BaseModel):
    first_name: str
    last_name: str
    avatar: Optional[Any]

    @validator("avatar", pre=True)
    def assemble_image_url(cls, v):
        if v:
            return FileProcessor.generate_file_url(
                key=v.id, folder="avatars", content_type=v.resource_type
            )
        return None

    class Config:
        orm_mode = True


class ProfileResponseSchema(ResponseSchema):
    data: ProfileDataSchema


# ---------------------------------------- #
