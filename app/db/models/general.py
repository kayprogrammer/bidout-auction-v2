from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
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


class Subscriber(BaseModel):
    __tablename__ = "subscribers"

    email = Column(String, unique=True)
    exported = Column(Boolean, default=False)

    def __repr__(self):
        return self.email


class Review(BaseModel):
    __tablename__ = "reviews"

    reviewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    reviewer = relationship("User", lazy="joined")
    show = Column(Boolean, default=False)
    text = Column(String(200))

    def __repr__(self):
        return self.reviewer_id
