from pydantic import BaseModel, validator, Field, EmailStr
from typing import Optional
from uuid import UUID

from app.api.utils.file_processors import FileProcessor
from app.core.database import SessionLocal
from app.db.managers.accounts import user_manager

from .base import ResponseSchema

# Site Details
class SiteDetailDataSchema(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    fb: str
    tw: str
    wh: str
    ig: str

    class Config:
        orm_mode = True


class SiteDetailResponseSchema(ResponseSchema):
    data: SiteDetailDataSchema


# -----------------------------

# Suscribers
class SuscriberSchema(BaseModel):
    email: EmailStr = Field("johndoe@example.com")

    class Config:
        orm_mode = True


class SuscriberResponseSchema(ResponseSchema):
    data: SuscriberSchema


# ----------------------

# Reviews
class ReviewsDataSchema(BaseModel):
    reviewer_id: UUID
    reviewer: Optional[dict]
    text: str

    @validator("reviewer", always=True)
    def show_reviewer(cls, v, values):
        db = SessionLocal()
        reviewer_id = values.get("reviewer_id")
        reviewer = user_manager.get_by_id(db, reviewer_id)
        values.pop("reviewer_id", None)
        if reviewer:
            avatar = None
            if reviewer.avatar_id:
                avatar = FileProcessor.generate_file_url(
                    key=reviewer.avatar_id,
                    folder="reviewers",
                    content_type=reviewer.avatar.resource_type,
                )
            db.close()
            return {"name": reviewer.full_name(), "avatar": avatar}
        db.close()
        return v

    class Config:
        orm_mode = True


class ReviewsResponseSchema(ResponseSchema):
    data: SiteDetailDataSchema


# ---------------------------------
