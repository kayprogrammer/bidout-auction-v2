from app.core.config import settings
from app.db.managers.accounts import user_manager
from app.db.managers.general import sitedetail_manager, review_manager
from app.db.managers.listings import category_manager, listing_manager
from app.db.managers.base import file_manager
from app.api.utils.file_processors import FileProcessor

from sqlalchemy.orm import Session
from pathlib import Path
from .mappings import listing_mappings, category_mappings, file_mappings
from datetime import datetime, timedelta
from slugify import slugify
import os
import random

CURRENT_DIR = Path(__file__).resolve().parent
test_images_directory = os.path.join(CURRENT_DIR, "images")


class CreateData(object):
    def __init__(self, db: Session) -> None:
        self.create_superuser(db)
        auctioneer = self.create_auctioneer(db)
        reviewer = self.create_reviewer(db)
        self.create_sitedetail(db)
        self.create_reviews(db, reviewer.id)
        category_ids = self.create_categories(db)
        self.create_listings(db, category_ids, auctioneer.id)

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

    def create_categories(self, db) -> None:
        category_ids = category_manager.get_all_ids(db)
        if len(category_ids) < 1:
            category_ids = category_manager.bulk_create(db, category_mappings)
        return category_ids

    def create_listings(self, db, category_ids, auctioneer_id) -> None:
        listings = listing_manager.get_all(db)
        if len(listings) < 1:
            image_ids = file_manager.bulk_create(db, file_mappings)
            updated_listing_mappings = []
            for idx, mapping in enumerate(listing_mappings):
                mapping.update(
                    {
                        "slug": slugify(mapping["name"]),
                        "category_id": random.choice(category_ids),
                        "desc": "Korem ipsum dolor amet, consectetur adipiscing elit. Maece nas in pulvinar neque. Nulla finibus lobortis pulvinar. Donec a consectetur nulla.",
                        "auctioneer_id": auctioneer_id,
                        "closing_date": datetime.now() + timedelta(days=7 + idx),
                        "image_id": image_ids[idx],
                    }
                )
                updated_listing_mappings.append(mapping)
            listing_manager.bulk_create(db, updated_listing_mappings)

            # Upload Images
            for idx, image_file in enumerate(os.listdir(test_images_directory)):
                image_path = os.path.join(test_images_directory, image_file)
                FileProcessor.upload_file(image_path, str(image_ids[idx]), "listings")
        pass
