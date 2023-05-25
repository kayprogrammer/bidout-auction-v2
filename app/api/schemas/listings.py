from typing import Optional, List, Any

from pydantic import BaseModel, validator, Field
from datetime import datetime
from uuid import UUID
from .base import ResponseSchema

from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.db.managers.listings import category_manager

from app.api.utils.file_processors import FileProcessor

from app.core.database import SessionLocal

from decimal import Decimal

# LISTINGS


class AddOrRemoveWatchlistSchema(BaseModel):
    slug: str = Field(..., example="listing_slug")


class ListingDataSchema(BaseModel):
    name: str

    auctioneer_id: UUID = Field(..., example="Ignore this")
    auctioneer: Optional[dict] = Field(
        None, example={"name": "John Doe", "avatar": "https://image.url"}
    )

    slug: Optional[str]
    desc: str

    category_id: Optional[UUID] = Field(..., example="Ignore this")
    category: Optional[str]

    price: Decimal = Field(..., example=1000.00, decimal_places=2)
    closing_date: datetime
    active: bool
    bids_count: int
    image_id: UUID = Field(..., example="Ignore this")
    image: Optional[Any]
    watchlist: Optional[bool]

    @validator("closing_date", always=True)
    def assemble_closing_date(cls, v):
        return v.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

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
                    folder="avatars",
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

    @validator("image", always=True)
    def assemble_image_url(cls, v, values):
        db = SessionLocal()
        image_id = values.get("image_id")
        file = file_manager.get_by_id(db, image_id)
        if file:
            db.close()
            values.pop("image_id", None)
            file_url = FileProcessor.generate_file_url(
                key=image_id,
                folder="listings",
                content_type=file.resource_type,
            )
            return file_url
        db.close()
        values.pop("image_id", None)
        return None

    class Config:
        orm_mode = True


class ListingResponseSchema(ResponseSchema):
    data: ListingDataSchema


class ListingsResponseSchema(ResponseSchema):
    data: List[ListingDataSchema]


# ------------------------------------------------------ #

# CATEGORIES
class CategoryDataSchema(BaseModel):
    name: str
    slug: str

    class Config:
        orm_mode = True


class CategoriesResponseSchema(ResponseSchema):
    data: List[CategoryDataSchema]


# ------------------------------------------------------ #


# BIDS #
class CreateBidSchema(BaseModel):
    amount: Decimal = Field(..., example=1000.00, decimal_places=2)


class BidDataSchema(BaseModel):
    id: UUID
    user_id: UUID = Field(..., example="Ignore this")
    user: Optional[dict] = Field(
        None, example={"name": "John Doe", "avatar": "https://image.url"}
    )
    amount: Decimal = Field(..., example=1000.00, decimal_places=2)
    created_at: datetime
    updated_at: datetime

    @validator("created_at", "updated_at", always=True)
    def assemble_date(cls, v):
        return v.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @validator("user", always=True)
    def show_user(cls, v, values):
        db = SessionLocal()
        user_id = values.get("user_id")
        user = user_manager.get_by_id(db, user_id)
        values.pop("user_id", None)
        if user:
            avatar = None
            if user.avatar_id:
                avatar = FileProcessor.generate_file_url(
                    key=user.avatar_id,
                    folder="avatars",
                    content_type=user.avatar.resource_type,
                )
            db.close()
            return {"name": user.full_name(), "avatar": avatar}
        db.close()
        return v

    class Config:
        orm_mode = True


class BidResponseSchema(ResponseSchema):
    data: BidDataSchema


class BidsResponseSchema(ResponseSchema):
    data: List[BidDataSchema]


# -------------------------------------------- #
