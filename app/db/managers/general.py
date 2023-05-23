from typing import Optional
from sqlalchemy.orm import Session

from app.db.managers.base import BaseManager
from app.db.models.general import SiteDetail, Subscriber, Review


class SiteDetailManager(BaseManager[SiteDetail]):
    def get(self, db: Session) -> Optional[SiteDetail]:
        sitedetail = db.query(self.model).first()
        if not sitedetail:
            sitedetail = self.create(db, {})
        return sitedetail


class SubscriberManager(BaseManager[Subscriber]):
    def get_by_email(self, db: Session, email: str) -> Optional[Subscriber]:
        subscriber = db.query(self.model).filter_by(email=email).first()
        return subscriber


class ReviewManager(BaseManager[Review]):
    def get_active(self, db: Session) -> Optional[Review]:
        reviews = db.query(self.model).filter_by(show=True).all()
        return reviews

    def get_count(self, db: Session) -> Optional[int]:
        reviews_count = db.query(self.model).filter_by(show=True).count()
        return reviews_count


sitedetail_manager = SiteDetailManager(SiteDetail)
subscriber_manager = SubscriberManager(Subscriber)
review_manager = ReviewManager(Review)
