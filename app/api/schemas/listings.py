from typing import Optional, List

from pydantic import BaseModel, validator, Field
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from .base import ResponseSchema
from app.db.managers.listings import listing_manager, category_manager
from app.db.managers.accounts import user_manager

from app.core.database import SessionLocal

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

    price: int
    closing_date: datetime
    active: bool
    bids_count: int
    # image: str

    @validator("auctioneer", pre=True)
    def show_auctioneer(cls, v, values):
        db = SessionLocal()
        auctioneer_id = values.get("auctioneer_id")
        auctioneer = listing_manager.get_by_id(db, auctioneer_id)
        values.pop("auctioneer_id", None)
        db.close()
        return {"name": auctioneer.full_name(), "avatar": ""} if auctioneer else None

    @validator("category", pre=True)
    def show_category(cls, v, values):
        db = SessionLocal()
        category_id = values.get("category_id")
        category = category_manager.get_by_id(db, category_id)
        values.pop("category_id", None)
        db.close()
        return category.name if category else "Other"

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
    amount: int


class BidDataSchema(BaseModel):
    id: UUID
    user: dict = {}
    user_id: UUID
    amount: int
    created_at: datetime
    updated_at: datetime

    @validator("user", pre=True)
    def show_user(cls, v, values):
        db = SessionLocal()
        user_id = values.get("user_id")
        user = user_manager.get_by_id(db, user_id)
        values.pop("user_id", None)
        db.close()
        return {"name": user.full_name(), "avatar": ""} if user else None


class BidResponseSchema(ResponseSchema):
    data: BidDataSchema


class BidsResponseSchema(ResponseSchema):
    data: List[BidDataSchema]


# -------------------------------------------- #
