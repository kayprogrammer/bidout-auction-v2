from typing import Optional

from pydantic import BaseModel, validator, Field
from datetime import datetime
from uuid import UUID
from .base import ResponseSchema
from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.db.managers.listings import listing_manager

from app.core.database import SessionLocal
from app.api.utils.file_types import ALLOWED_IMAGE_TYPES
from app.api.utils.file_processors import FileProcessor


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

    @validator("file_type")
    def validate_file_type(cls, v):
        if not v in ALLOWED_IMAGE_TYPES:
            raise ValueError("Image type not allowed!")
        return v


class CreateListingResponseDataSchema(BaseModel):
    name: str
    auctioneer: dict = {}
    auctioneer_id: UUID

    slug: str = None
    desc: str
    category: Optional[str]
    category_id: UUID

    price: int
    closing_date: datetime
    active: bool
    bids_count: int
    image_id: UUID
    upload_url: str

    @validator("upload_url", pre=True)
    def assemble_upload_url(cls, v, values):
        db = SessionLocal()
        image_id = values.get("image_id")
        file = file_manager.get_by_id(db, image_id)
        if file:
            db.close()
            values.pop("image_id", None)
            return FileProcessor.generate_file_url(
                key=image_id, folder="listings", content_type=file.resource_type
            )
        db.close()
        values.pop("image_id", None)
        return None

    @validator("auctioneer", pre=True)
    def show_auctioneer(cls, v, values):
        db = SessionLocal()
        auctioneer_id = values.get("auctioneer_id")
        auctioneer = listing_manager.get_by_id(db, auctioneer_id)
        values.pop("auctioneer_id", None)
        db.close()
        if auctioneer:
            avatar = FileProcessor.generate_file_url(
                key=auctioneer.avatar_id,
                folder="user",
                content_type=auctioneer.avatar.resource_type,
            )
            return {"name": auctioneer.full_name(), "avatar": avatar}
        return v

    @validator("category", pre=True)
    def show_category(cls, v, values):
        db = SessionLocal()
        category_id = values.get("category_id")
        category = category_manager.get_by_id(db, category_id)
        values.pop("category_id", None)
        db.close()
        return category.name if category else "Other"


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
