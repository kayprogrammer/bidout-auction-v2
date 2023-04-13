from pydantic import BaseModel, validator, Field, EmailStr
from app.core.database import SessionLocal
from app.db.managers.accounts import user_manager


class RegisterUserSchema(BaseModel):
    first_name: str = Field("John", max_length=50)
    last_name: str = Field("Doe", max_length=50)
    email: EmailStr = Field("johndoe@example.com")
    password: str = Field("strongpassword", min_length=8)

    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.split(" ")) > 1:
            raise ValueError("No spacing allowed")
        return v

    @validator("email")
    def validate_email(cls, v):
        db = SessionLocal()
        existing_user = user_manager.get_by_email(db, v)
        if existing_user:
            db.close()
            raise ValueError("Email already registered!")
        db.close()
        return v

    class Config:
        error_msg_templates = {
            "value_error.any_str.max_length": "50 characters max!",
            "value_error.any_str.min_length": "8 characters min!",
        }


class VerifyOtpSchema(BaseModel):
    email: EmailStr = Field("johndoe@example.com")
    otp: int


class RequestOtpSchema(BaseModel):
    email: EmailStr = Field("johndoe@example.com")


class SetNewPasswordSchema(BaseModel):
    password: str = Field("newstrongpassword", min_length=8)

    class Config:
        error_msg_templates = {
            "value_error.any_str.min_length": "8 characters min!",
        }


class LoginUserSchema(BaseModel):
    email: EmailStr = Field("johndoe@example.com")
    password: str = Field("password")


class RefreshTokensSchema(BaseModel):
    refresh: str
