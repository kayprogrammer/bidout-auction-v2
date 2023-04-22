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
    name = Column(String(70))
    slug = Column(String(), unique=True)
    desc = Column(Text())
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    price = Column(Numeric(precision=10, scale=2))
    closing_date = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    bids_count = Column(Integer, default=0)

    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        unique=True,
    )
    image = relationship(
        "File", foreign_keys=[image_id], back_populates="listing_image"
    )

    listing_bids = relationship(
        "Bid",
        foreign_keys="Bid.listing_id",
        back_populates="listing",
        lazy="dynamic",
    )
    listing_watchlists = relationship(
        "WatchList",
        foreign_keys="WatchList.listing_id",
        back_populates="listing",
    )

    def __repr__(self):
        return self.name

    def time_left(self):
        remaining_time = self.closing_date - datetime.utcnow()
        remaining_seconds = remaining_time.total_seconds()

        if self.active == False or remaining_seconds < 0:
            return "Closed!!!"
        else:
            days, seconds = divmod(int(remaining_seconds), 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            return f"-{days:02d}D :{hours:02d}H :{minutes:02d}M :{seconds:02d}S"

    def time_left_seconds(self):
        if not self.active:
            return 0
        remaining_time = self.closing_date - datetime.utcnow()
        remaining_seconds = remaining_time.total_seconds()
        return remaining_seconds

    def get_highest_bid(self):
        highest_bid = 0.00
        related_bids = self.listing_bids
        if related_bids:
            highest_bid = (
                related_bids.session.query(func.max(Bid.amount))
                .filter_by(listing_id=self.id)
                .scalar()
            )
            highest_bid = related_bids.filter_by(amount=highest_bid).first()
            if highest_bid:
                highest_bid = highest_bid.amount
            else:
                highest_bid = 0.00

        return highest_bid


class Bid(BaseModel):
    __tablename__ = "bids"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    listing_id = Column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    listing = relationship(
        "Listing", foreign_keys=[listing_id], back_populates="listing_bids"
    )
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
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="user_watchlists"
    )

    listing_id = Column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    listing = relationship(
        "Listing",
        foreign_keys=[listing_id],
        back_populates="listing_watchlists",
    )

    session_key = Column(String)

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
