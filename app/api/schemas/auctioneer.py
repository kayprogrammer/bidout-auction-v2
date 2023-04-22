from typing import Optional, Any

from pydantic import BaseModel, validator, Field, StrictStr, root_validator
from datetime import datetime
from uuid import UUID
from .base import ResponseSchema
from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.db.managers.listings import listing_manager, category_manager

from app.core.database import SessionLocal
from app.api.utils.file_types import ALLOWED_IMAGE_TYPES
from app.api.utils.file_processors import FileProcessor
from pytz import UTC
from decimal import Decimal

# CREATE LISTING #


class CreateListingSchema(BaseModel):
    name: StrictStr = Field("Product name", max_length=70)
    desc: str = Field("Product description")
    category: Optional[StrictStr] = Field("category_slug")
    price: Decimal = Field(1000.00, decimal_places=2)
    closing_date: datetime
    file_type: str = Field("image/jpeg")

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
    auctioneer_id: UUID
    auctioneer: Optional[dict]

    slug: str
    desc: str

    category_id: UUID
    category: Optional[str]

    price: int
    closing_date: Any
    active: bool
    bids_count: int
    image_id: UUID
    upload_url: Optional[str]

    @validator("upload_url", always=True)
    def assemble_upload_url(cls, v, values):
        db = SessionLocal()
        image_id = values.get("image_id")
        file = file_manager.get_by_id(db, image_id)
        if file:
            db.close()
            values.pop("image_id", None)
            return FileProcessor.generate_file_url(
                key=image_id,
                folder="listings",
                content_type=file.resource_type,
            )
        db.close()
        values.pop("image_id", None)
        return None

    @validator("auctioneer", always=True)
    def show_auctioneer(cls, v, values):
        db = SessionLocal()
        auctioneer_id = values.get("auctioneer_id")
        auctioneer = user_manager.get_by_id(db, auctioneer_id)
        values.pop("auctioneer_id", None)
        if auctioneer:
            avatar = None
            if auctioneer.avatar_id:
                avatar = FileProcessor.generate_file_url(
                    key=auctioneer.avatar_id,
                    folder="user",
                    content_type=auctioneer.avatar.resource_type,
                )
            db.close()
            return {"name": auctioneer.full_name(), "avatar": avatar}
        db.close()
        return v

    @validator("category", always=True)
    def show_category(cls, v, values):
        db = SessionLocal()
        category_id = values.get("category_id")
        category = category_manager.get_by_id(db, category_id)
        values.pop("category_id", None)
        db.close()
        return category.name if category else "Other"

    class Config:
        orm_mode = True


class CreateListingResponseSchema(ResponseSchema):
    data: CreateListingResponseDataSchema


# ---------------------------------------------------------- #

# USER PROFILE #


class UpdateProfileSchema(BaseModel):
    first_name: str = Field("John", max_length=50)
    last_name: str = Field("Doe", max_length=50)
    file_type: str = Field("image/png")

    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.split(" ")) > 1:
            raise ValueError("No spacing allowed")
        return v

    @validator("file_type")
    def validate_file_type(cls, v):
        if not v in ALLOWED_IMAGE_TYPES:
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
    avatar_id: UUID
    upload_url: Optional[str]

    @validator("upload_url", always=True)
    def assemble_upload_url(cls, v, values):
        db = SessionLocal()
        avatar_id = values.get("avatar_id")
        file = file_manager.get_by_id(db, avatar_id)
        if file:
            db.close()
            values.pop("avatar_id", None)
            return FileProcessor.generate_file_url(
                key=avatar_id,
                folder="avatar",
                content_type=file.resource_type,
            )
        db.close()
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
    avatar_id: Optional[UUID]  # This must be above avatar field
    avatar: Optional[Any]

    @validator("avatar", always=True)
    def assemble_image_url(cls, v, values):
        db = SessionLocal()
        avatar_id = values.get("avatar_id")
        file = file_manager.get_by_id(db, avatar_id)
        if file:
            db.close()
            values.pop("avatar_id", None)
            return FileProcessor.generate_file_url(
                key=avatar_id, folder="avatar", content_type=file.resource_type
            )
        db.close()
        values.pop("avatar_id", None)
        return None

    class Config:
        orm_mode = True


class ProfileResponseSchema(ResponseSchema):
    data: ProfileDataSchema


# ---------------------------------------- #