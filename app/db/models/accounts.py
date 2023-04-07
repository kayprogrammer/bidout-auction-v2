from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from datetime import datetime


class Timezone(BaseModel):
    __tablename__ = "timezones"
    name = Column(String())
    user_timezones = relationship(
        "User", foreign_keys="User.tz_id", back_populates="timezone", lazy=True
    )

    def __repr__(self):
        return str(self.name)


class User(BaseModel):
    __tablename__ = "users"
    first_name = Column(String(50))
    last_name = Column(String(50))

    email = Column(String(), unique=True)

    password = Column(String())
    tz_id = Column(UUID(as_uuid=True), ForeignKey("timezones.id", ondelete="SET NULL"))
    timezone = relationship(
        "Timezone", foreign_keys=[tz_id], back_populates="user_timezones"
    )

    is_email_verified = Column(Boolean(), default=False)
    is_superuser = Column(Boolean(), default=False)
    is_staff = Column(Boolean(), default=False)

    jwt = relationship(
        "Jwt",
        foreign_keys="Jwt.user_id",
        back_populates="user",
        lazy=True,
        uselist=False,
    )

    otp = relationship(
        "Otp",
        foreign_keys="Otp.user_id",
        back_populates="user",
        lazy=True,
        uselist=False,
    )

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return self.get_full_name()


class Jwt(BaseModel):
    __tablename__ = "jwts"
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    user = relationship("User", foreign_keys=[user_id], back_populates="jwt")
    access = Column(String())
    refresh = Column(String())

    def __repr__(self):
        return f"Access - {self.access} | Refresh - {self.refresh}"


class Otp(BaseModel):
    __tablename__ = "otps"
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    user = relationship("User", foreign_keys=[user_id], back_populates="otp")
    code = Column(Integer())

    def __repr__(self):
        return f"User - {self.user.get_full_name} | Code - {self.code}"

    def check_expiration(self):
        now = datetime.utcnow()
        diff = now - self.updated_at
        if diff.total_seconds() > 900:
            return True
        return False
