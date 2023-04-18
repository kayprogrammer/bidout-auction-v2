from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.managers.base import BaseManager
from app.db.models.accounts import Jwt, Otp, User
from uuid import UUID
import random


class UserManager(BaseManager[User]):
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        user = db.query(self.model).filter_by(email=email).first()
        return user

    def create(self, db: Session, obj_in) -> User:
        # hash the password
        obj_in.update({"password": get_password_hash(obj_in["password"])})
        return super().create(db, obj_in)

    def update(self, db: Session, db_obj, obj_in) -> Optional[User]:
        # hash the password
        password = obj_in.get("password")
        if password:
            obj_in["password"] = get_password_hash(password)
        return super().update(db, db_obj, obj_in)


class OtpManager(BaseManager[Otp]):
    def get_by_user_id(self, db: Session, user_id: str) -> Optional[Otp]:
        jwt = db.query(self.model).filter_by(user_id=user_id).first()
        return jwt

    def create(self, db: Session, obj_in) -> Optional[Otp]:
        code = random.randint(100000, 999999)
        obj_in.update({"code": code})
        existing_otp = self.get_by_user_id(db, obj_in["user_id"])
        if existing_otp:
            return self.update(db, existing_otp, {"code": code})
        return super().create(db, obj_in)


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
otp_manager = OtpManager(Otp)
jwt_manager = JwtManager(Jwt)


# this can now be used to perform any available crud actions e.g user_manager.get_by_id(db=db, id=id)
