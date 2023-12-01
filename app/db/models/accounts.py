from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from datetime import datetime
from app.core.config import settings
from app.db.models.listings import WatchList


class User(BaseModel):
    __tablename__ = "users"
    first_name = Column(String(50))
    last_name = Column(String(50))

    email = Column(String(), unique=True)

    password = Column(String())
    is_email_verified = Column(Boolean(), default=False)
    is_superuser = Column(Boolean(), default=False)
    is_staff = Column(Boolean(), default=False)
    terms_agreement = Column(Boolean(), default=False)

    avatar_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        unique=True,
    )
    avatar = relationship("File", lazy="joined")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return self.full_name()

    @property
    def is_authenticated(self):
        return True


class Jwt(BaseModel):
    __tablename__ = "jwts"
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    user = relationship("User", lazy="joined")
    access = Column(String())
    refresh = Column(String())

    def __repr__(self):
        return f"Access - {self.access} | Refresh - {self.refresh}"


class Otp(BaseModel):
    __tablename__ = "otps"
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    user = relationship("User", lazy="joined")
    code = Column(Integer())

    def __repr__(self):
        return f"User - {self.user.get_full_name} | Code - {self.code}"

    def check_expiration(self):
        now = datetime.utcnow()
        diff = now - self.updated_at
        if diff.total_seconds() > settings.EMAIL_OTP_EXPIRE_SECONDS:
            return True
        return False
