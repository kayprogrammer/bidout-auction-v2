from app.core.config import settings
from app.db.managers.accounts import user_manager
from sqlalchemy.orm import Session


class CreateData(object):
    def __init__(self, db: Session) -> None:
        self.create_superuser(db)
        self.create_auctioneer(db)

    def create_superuser(self, db) -> None:
        superuser = user_manager.get_by_email(db, settings.FIRST_SUPERUSER_EMAIL)
        user_dict = {
            "first_name": "Test",
            "last_name": "Admin",
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "is_superuser": True,
            "is_staff": True,
            "is_email_verified": True,
        }
        if not superuser:
            superuser = user_manager.create(db, user_dict)
        return superuser

    def create_auctioneer(self, db) -> None:
        auctioneer = user_manager.get_by_email(db, settings.FIRST_AUCTIONEER_EMAIL)
        user_dict = {
            "first_name": "Test",
            "last_name": "Auctioneer",
            "email": settings.FIRST_AUCTIONEER_EMAIL,
            "password": settings.FIRST_AUCTIONEER_PASSWORD,
            "is_email_verified": True,
        }
        if not auctioneer:
            auctioneer = user_manager.create(db, user_dict)
        return auctioneer
