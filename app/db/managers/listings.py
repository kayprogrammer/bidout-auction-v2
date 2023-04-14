from typing import Optional, List
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.managers.base import BaseManager
from app.db.models.listings import Category, Listing, WatchList, Bid
from app.api.utils.tokens import get_random
from uuid import UUID
from slugify import slugify


class CategoryManager(BaseManager[Category]):
    def get_by_name(self, db: Session, name: str) -> Optional[Category]:
        category = db.query(self.model).filter_by(name=name).first()
        return category

    def get_by_slug(self, db: Session, slug: str) -> Optional[Category]:
        category = db.query(self.model).filter_by(slug=slug).first()
        return category

    def create(self, db: Session, obj_in) -> Optional[Category]:
        # Generate unique slug
        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug

        obj_in["slug"] = slug
        slug_exists = self.get_by_slug(db, slug)
        if slug_exists:
            random_str = get_random(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return self.create(db, obj_in)

        return super().create(db, obj_in)


class ListingManager(BaseManager[Listing]):
    def get_by_auctioneer_id(
        self, db: Session, auctioneer_id: UUID
    ) -> Optional[Listing]:
        listings = db.query(self.model).filter_by(auctioneer_id=auctioneer_id).all()
        return listings

    def get_by_slug(self, db: Session, slug: str) -> Optional[Listing]:
        listing = db.query(self.model).filter_by(slug=slug).first()
        return listing

    def get_by_category(
        self, db: Session, category: Optional[Category]
    ) -> Optional[Listing]:
        listings = []
        if category:
            listings = db.query(self.model).filter_by(category_id=category.id).all()
        else:
            listings = db.query(self.model).filter_by(category_id=None).all()
        return listings

    def create(self, db: Session, obj_in) -> Optional[Listing]:
        # Generate unique slug

        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug
        obj_in["slug"] = slug
        slug_exists = self.get_by_slug(db, slug)
        if slug_exists:
            random_str = get_random(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return self.create(db, obj_in)

        return super().create(db, obj_in)

    def update(self, db: Session, db_obj: Listing, obj_in) -> Optional[Listing]:
        # Generate unique slug

        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug
        obj_in["slug"] = slug
        slug_exists = self.get_by_slug(db, slug)
        if slug_exists and not slug == db_obj.slug:
            random_str = get_random(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return self.update(db, db_obj, obj_in)

        return super().update(db, db_obj, obj_in)


class WatchListManager(BaseManager[WatchList]):
    def get_by_user_id_or_session_key(
        self, db: Session, id: UUID
    ) -> Optional[List[WatchList]]:
        print(type(id))
        watchlist = (
            db.query(self.model)
            .filter(or_(self.model.user_id == id, self.model.session_key == str(id)))
            .all()
        )
        return watchlist

    def get_by_user_id_or_session_key_and_listing_id(
        self, db: Session, id: UUID, listing_id: UUID
    ) -> Optional[List[WatchList]]:
        watchlist = (
            db.query(self.model)
            .filter(or_(self.model.user_id == id, self.model.session_key == str(id)))
            .filter(self.model.listing_id == listing_id)
            .first()
        )
        return watchlist

    def create(self, db: Session, obj_in: dict):
        user_id = obj_in.get("user_id")
        session_key = obj_in.get("session_key")
        listing_id = obj_in["listing_id"]
        key = user_id if user_id else session_key

        # Avoid duplicates
        existing_watchlist = (
            watchlist_manager.get_by_user_id_or_session_key_and_listing_id(
                db, key, listing_id
            )
        )
        if existing_watchlist:
            return existing_watchlist
        return super().create(db, obj_in)


class BidManager(BaseManager[Bid]):
    def get_by_user_id(self, db: Session, user_id: UUID) -> Optional[List[Bid]]:
        bids = db.query(self.model).filter_by(user_id=user_id).all()
        return bids

    def get_by_listing_id(self, db: Session, listing_id: UUID) -> Optional[List[Bid]]:
        bids = db.query(self.model).filter_by(listing_id=listing_id).all()
        return bids

    def get_by_user_and_listing_id(
        self, db: Session, user_id: UUID, listing_id: UUID
    ) -> Optional[List[Bid]]:
        bid = (
            db.query(self.model)
            .filter_by(user_id=user_id, listing_id=listing_id)
            .first()
        )
        return bid

    def create(self, db: Session, obj_in: dict):
        user_id = obj_in["user_id"]
        listing_id = obj_in["listing_id"]

        existing_bid = bid_manager.get_by_user_and_listing_id(db, user_id, listing_id)
        if existing_bid:
            obj_in.pop("user_id", None)
            obj_in.pop("listing_id", None)
            return self.update(db, existing_bid, obj_in)

        new_bid = super().create(db, obj_in)
        listing = new_bid.listing
        listing_manager.update(db, listing, {"bids_count": listing.bids_count + 1})
        return new_bid

    def delete(self, db: Session, db_obj: Bid):
        listing = db_obj.listing
        listing_manager.update(db, listing, {"bids_count": listing.bids_count - 1})
        return super().delete(db, db_obj)


# How to use
category_manager = CategoryManager(Category)
listing_manager = ListingManager(Listing)
watchlist_manager = WatchListManager(WatchList)
bid_manager = BidManager(Bid)


# this can now be used to perform any available crud actions e.g category_manager.get_by_id(db=db, id=id)
