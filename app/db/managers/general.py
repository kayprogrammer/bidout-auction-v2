from typing import Optional
from sqlalchemy.orm import Session

from app.db.managers.base import BaseManager
from app.db.models.general import SiteDetail, Suscriber, Review


class SiteDetailManager(BaseManager[SiteDetail]):
    def get(self, db: Session) -> Optional[SiteDetail]:
        sitedetail = db.query(self.model).first()
        if not sitedetail:
            sitedetail = self.create(db, {})
        return sitedetail


class SuscriberManager(BaseManager[Suscriber]):
    def get_by_email(self, db: Session, email: str) -> Optional[Suscriber]:
        suscriber = db.query(self.model).filter(email=email).first()
        return suscriber


class ReviewManager(BaseManager[Review]):
    pass


sitedetail_manager = SiteDetailManager(SiteDetail)
suscriber_manager = SuscriberManager(Suscriber)
review_manager = ReviewManager(Review)
