from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Numeric,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from .base import BaseModel
from datetime import datetime


class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String(30), unique=True)
    slug = Column(String(), unique=True)

    def __repr__(self):
        return self.name

    @validates("name")
    def validate_name(self, key, value):
        if value == "Other":
            raise ValueError("Name must not be 'Other'")
        return value


class Listing(BaseModel):
    __tablename__ = "listings"

    auctioneer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    auctioneer = relationship("User", lazy="joined")

    name = Column(String(70))
    slug = Column(String(), unique=True)
    desc = Column(Text())
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    category = relationship("Category", lazy="joined")

    price = Column(Numeric(precision=10, scale=2))
    highest_bid = Column(Numeric(precision=10, scale=2), default=0.00)
    bids_count = Column(Integer, default=0)
    closing_date = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        unique=True,
    )
    image = relationship("File", lazy="joined")

    def __repr__(self):
        return self.name

    @property
    def time_left_seconds(self):
        remaining_time = self.closing_date - datetime.utcnow()
        remaining_seconds = remaining_time.total_seconds()
        return remaining_seconds

    @property
    def time_left(self):
        if not self.active:
            return 0
        return self.time_left_seconds


class Bid(BaseModel):
    __tablename__ = "bids"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", lazy="joined")
    listing_id = Column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    listing = relationship("Listing", lazy="joined")
    amount = Column(Numeric(precision=10, scale=2))

    def __repr__(self):
        return f"{self.listing.name} - ${self.amount}"

    __table_args__ = (
        UniqueConstraint("listing_id", "amount", name="unique_listing_amount_bids"),
        UniqueConstraint("user_id", "listing_id", name="unique_user_listing_bids"),
    )


class WatchList(BaseModel):
    __tablename__ = "watchlists"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", lazy="joined")

    listing_id = Column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    listing = relationship("Listing", lazy="joined")

    session_key = Column(
        UUID(as_uuid=True), ForeignKey("guestusers.id", ondelete="CASCADE")
    )

    def __repr__(self):
        if self.user:
            return f"{self.listing.name} - {self.user.full_name()}"
        return f"{self.listing.name} - {self.session_key}"

    __table_args__ = (
        UniqueConstraint(
            "user_id", "listing_id", name="unique_user_listing_watchlists"
        ),
        UniqueConstraint(
            "session_key",
            "listing_id",
            name="unique_session_key_listing_watchlists",
        ),
    )
