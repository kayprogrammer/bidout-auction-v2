from app.core.config import settings
from app.db.managers.accounts import user_manager
from app.db.managers.general import sitedetail_manager, review_manager

from sqlalchemy.orm import Session


class CreateData(object):
    def __init__(self, db: Session) -> None:
        self.create_superuser(db)
        self.create_auctioneer(db)
        reviewer = self.create_reviewer(db)
        self.create_sitedetail(db)
        self.create_reviews(db, reviewer.id)

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

    def create_reviewer(self, db) -> None:
        reviewer = user_manager.get_by_email(db, settings.FIRST_REVIEWER_EMAIL)
        user_dict = {
            "first_name": "Test",
            "last_name": "Reviewer",
            "email": settings.FIRST_REVIEWER_EMAIL,
            "password": settings.FIRST_REVIEWER_PASSWORD,
            "is_email_verified": True,
        }
        if not reviewer:
            reviewer = user_manager.create(db, user_dict)
        return reviewer

    def create_sitedetail(self, db) -> None:
        sitedetail = sitedetail_manager.get(db)
        if not sitedetail:
            sitedetail = sitedetail_manager.create(db, {})
        return sitedetail

    def create_reviews(self, db, reviewer_id) -> None:
        reviews_count = review_manager.get_count(db)
        if reviews_count < 1:
            review_manager.bulk_create(db, self.review_mappings(reviewer_id))
        pass

    def review_mappings(self, reviewer_id):
        return [
            {
                "reviewer_id": reviewer_id,
                "text": "Maecenas vitae porttitor neque, ac porttitor nunc. Duis venenatis lacinia libero. Nam nec augue ut nunc vulputate tincidunt at suscipit nunc.",
                "show": True,
            },
            {
                "reviewer_id": reviewer_id,
                "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                "show": True,
            },
            {
                "reviewer_id": reviewer_id,
                "text": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
                "show": True,
            },
        ]
