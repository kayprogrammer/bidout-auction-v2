import re
from typing import Optional

from pydantic import BaseModel, validator, Field
from app.core.database import SessionLocal
from app.db.managers.accounts import user_manager


def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    email_valid = bool(re.match(pattern, email))
    if not email_valid:
        raise ValueError("Invalid email!")
    return email


class RegisterUserSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v):
        validate_email(v)
        db = SessionLocal()
        existing_user = user_manager.get_by_email(db, v)
        if existing_user:
            db.close()
            raise ValueError("Email already registered!")
        db.close()
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        return v


class VerifyOtpSchema(BaseModel):
    email: str
    otp: int

    @validator("email")
    def validate_email(cls, v):
        return validate_email(v)


class RequestOtpSchema(BaseModel):
    email: str

    @validator("email")
    def validate_email(cls, v):
        return validate_email(v)


class SetNewPasswordSchema(BaseModel):
    password: str

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        return v


class LoginUserSchema(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode = True
