import re
from typing import Optional

from pydantic import BaseModel, EmailStr, validator
from .base import ResponseSchema


class RegisterUserSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        return v


class LoginUserSchema(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


class LoginResponseDataSchema(BaseModel):
    access: str
    refresh: str


class LoginResponseSchema(ResponseSchema):
    data: LoginResponseDataSchema
