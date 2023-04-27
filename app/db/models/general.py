from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
)

from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class SiteDetail(BaseModel):
    __tablename__ = "sitedetails"

    name = Column(String(300), default="Kay's Auction House")
    email = Column(String(300), default="kayprogrammer1@gmail.com")
    phone = Column(String(300), default="+2348133831036")
    address = Column(String(300), default="234, Lagos, Nigeria")
    fb = Column(String(300), default="https://facebook.com")
    tw = Column(String(300), default="https://twitter.com")
    wh = Column(
        String(300),
        default="https://wa.me/2348133831036",
    )
    ig = Column(String(300), default="https://instagram.com")

    def __repr__(self):
        return self.name


class Suscriber(BaseModel):
    __tablename__ = "suscribers"

    email = Column(String)
    exported = Column(Boolean, default=False)

    def __repr__(self):
        return self.email


class Review(BaseModel):
    __tablename__ = "reviews"

    reviewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    show = Column(Boolean, default=False)
    text = Column(String(100))

    def __repr__(self):
        return self.reviewer_id
