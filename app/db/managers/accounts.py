from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.managers.base import BaseManager
from app.db.models.accounts import Jwt, Otp, Timezone, User
from uuid import UUID


class UserManager(BaseManager[User]):
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        user = db.query(self.model).filter_by(email=email).first()
        return user

    def create(self, db: Session, obj_in) -> User:
        obj_in.update({"password": get_password_hash(obj_in["password"])})
        user_obj = self.model(**obj_in)
        db.add(user_obj)
        db.commit()
        db.refresh(user_obj)
        return user_obj

    def update(self, db: Session, db_obj, obj_in) -> Optional[User]:
        password = obj_in.get("password")
        if password:
            obj_in["password"] = get_password_hash(password)

        return super().update(db, db_obj, obj_in)


class TimezoneManager(BaseManager[Timezone]):
    def get_by_name(self, db: Session, name: str) -> Optional[Timezone]:
        timezone = db.query(self.model).filter_by(name=name).first()
        return timezone


class OtpManager(BaseManager[Otp]):
    def get_by_user_id(self, db: Session, user_id: str) -> Optional[Otp]:
        jwt = db.query(self.model).filter_by(user_id=user_id).first()
        return jwt


class JwtManager(BaseManager[Jwt]):
    def get_by_user_id(self, db: Session, user_id: str) -> Optional[Jwt]:
        jwt = db.query(self.model).filter_by(user_id=user_id).first()
        return jwt

    def get_by_refresh(self, db: Session, refresh: str) -> Optional[Jwt]:
        jwt = db.query(self.model).filter_by(refresh=refresh).first()
        return jwt

    def delete_by_user_id(self, db: Session, user_id: UUID):
        jwt = db.query(self.model).filter_by(user_id=user_id).first()
        if jwt:
            db.delete(jwt)
            db.commit()


# How to use
user_manager = UserManager(User)
timezone_manager = TimezoneManager(Timezone)
otp_manager = OtpManager(Otp)
jwt_manager = JwtManager(Jwt)


# this can now be used to perform any available crud actions e.g user_manager.get_by_id(db=db, id=id)
