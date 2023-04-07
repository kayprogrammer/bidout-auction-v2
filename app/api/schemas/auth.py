import re
from typing import Optional

from pydantic import BaseModel, validator, Field
from .base import ResponseSchema


class RegisterUserSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        email_valid = bool(re.match(pattern, v))
        if not email_valid:
            raise ValueError("Invalid email!")
        return v

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
