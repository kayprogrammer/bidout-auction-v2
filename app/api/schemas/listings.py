from typing import Optional

from pydantic import BaseModel, validator, Field
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from .base import ResponseSchema
from app.db.managers.listings import listing_manager, category_manager
from app.core.database import SessionLocal


class CreateListingSchema(BaseModel):
    name: str = Field(..., max_length=50)
    desc: str
    category_slug: Optional[str]
    price: int
    closing_date: datetime

    @validator("closing_date")
    def validate_closing_date(cls, v):
        if datetime.utcnow() > v:
            raise ValueError("Closing date must be beyond the current datetime!")
        return v


class CreateWatchlistSchema(BaseModel):
    listing_slug: str


class CreateBidSchema(BaseModel):
    listing_slug: str
    amount: Decimal = Field(ge=0.01, decimal_places=2)


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


class ListingsResponseSchema(ResponseSchema):
    data: ListingDataSchema
