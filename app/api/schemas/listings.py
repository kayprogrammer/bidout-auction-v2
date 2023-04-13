from typing import Optional, List

from pydantic import BaseModel, validator, Field
from datetime import datetime
from uuid import UUID
from .base import ResponseSchema

from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.db.managers.listings import listing_manager, category_manager

from app.api.utils.file_processors import FileProcessor

from app.core.database import SessionLocal

from decimal import Decimal

# LISTINGS


class CreateWatchlistSchema(BaseModel):
    slug: str


class ListingDataSchema(BaseModel):
    name: str
    auctioneer: dict = {}
    auctioneer_id: UUID

    slug: str = None
    desc: str
    category: Optional[str]
    category_id: UUID

    price: Decimal = Field(1000.00, decimal_places=2)
    closing_date: datetime
    active: bool
    bids_count: int
    image_id: UUID
    image: str = None

    @validator("auctioneer", pre=True)
    def show_auctioneer(cls, v, values):
        db = SessionLocal()
        auctioneer_id = values.get("auctioneer_id")
        auctioneer = listing_manager.get_by_id(db, auctioneer_id)
        values.pop("auctioneer_id", None)
        db.close()
        if auctioneer:
            avatar = None
            if auctioneer.avatar_id:
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

    @validator("image", pre=True)
    def assemble_image_url(cls, v, values):
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

    class Config:
        orm_mode = True


class ListingResponseSchema(ResponseSchema):
    data: ListingDataSchema


class ListingsResponseSchema(ResponseSchema):
    data: List[ListingDataSchema]


class ListingQuerySchema(BaseModel):
    quantity: Optional[int]


# ------------------------------------------------------ #


# BIDS #
class CreateBidSchema(BaseModel):
    amount: Decimal = Field(1000.00, decimal_places=2)


class BidDataSchema(BaseModel):
    id: UUID
    user: dict = {}
    user_id: UUID
    amount: Decimal = Field(1000.00, decimal_places=2)
    created_at: datetime
    updated_at: datetime

    @validator("user", pre=True)
    def show_user(cls, v, values):
        db = SessionLocal()
        user_id = values.get("user_id")
        user = user_manager.get_by_id(db, user_id)
        values.pop("user_id", None)
        db.close()
        if user:
            avatar = None
            if user.avatar_id:
                avatar = FileProcessor.generate_file_url(
                    key=user.avatar_id,
                    folder="user",
                    content_type=user.avatar.resource_type,
                )
            return {"name": user.full_name(), "avatar": avatar}
        return v


class BidResponseSchema(ResponseSchema):
    data: BidDataSchema


class BidsResponseSchema(ResponseSchema):
    data: List[BidDataSchema]


# -------------------------------------------- #
