from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.routes.deps import AuthUser, Client

from app.api.schemas.listings import (
    AddOrRemoveWatchlistSchema,
    ListingDataSchema,
    ListingsResponseSchema,
    ListingDetailDataSchema,
    ListingResponseSchema,
    CategoryDataSchema,
    CategoriesResponseSchema,
    CreateBidSchema,
    BidDataSchema,
    BidsResponseDataSchema,
    BidsResponseSchema,
    BidResponseSchema,
    ResponseSchema,
)
from app.api.utils.responses import ReqBody, ResBody
from app.common.responses import CustomResponse
from app.db.managers.listings import (
    listing_manager,
    bid_manager,
    watchlist_manager,
    category_manager,
)
from app.api.utils.decorators import validate_request
from app.api.utils.validators import validate_quantity

listings_router = Blueprint("Listings", url_prefix="/api/v2/listings")


class ListingsView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all listings",
        description="This endpoint retrieves all listings",
        response=ResBody(ListingsResponseSchema),
        parameter={"name": "quantity", "location": "query", "schema": int},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, db: AsyncSession, client: Client, **kwargs):
        quantity = validate_quantity(request.args.get("quantity"))
        listings = await listing_manager.get_all(db)
        if quantity:
            # Retrieve based on amount
            listings = listings[:quantity]

        data = [
            ListingDataSchema(
                watchlist=True
                if await watchlist_manager.get_by_client_id_and_listing_id(
                    db, client.id, listing.id
                )
                else False,
                time_left_seconds=listing.time_left_seconds,
                **listing.__dict__
            ).dict()
            for listing in listings
        ]
        return CustomResponse.success(message="Listings fetched", data=data)


class ListingDetailView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve listing's detail",
        description="This endpoint retrieves detail of a listing",
        response=ResBody(ListingResponseSchema),
    )
    @openapi.secured("token", "guest")
    async def get(self, request, db: AsyncSession, **kwargs):
        slug = kwargs["slug"]
        listing = await listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        related_listings = (
            await listing_manager.get_related_listings(db, listing.category_id, slug)
        )[:3]
        data = ListingDetailDataSchema(
            listing=ListingDataSchema.from_orm(listing),
            related_listings=[
                ListingDataSchema.from_orm(related_listing)
                for related_listing in related_listings
            ],
        ).dict()
        return CustomResponse.success(message="Listing details fetched", data=data)


class ListingsByWatchListView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all listings by users watchlist",
        description="This endpoint retrieves all listings in a user or guest watchlist",
        response=ResBody(ListingsResponseSchema),
    )
    @openapi.secured("token", "guest")
    async def get(self, request, db: AsyncSession, client: Client, **kwargs):
        watchlists = await watchlist_manager.get_by_client_id(db, client.id)
        data = [
            ListingDataSchema(
                watchlist=True,
                time_left_seconds=watchlist.listing.time_left_seconds,
                **watchlist.listing.__dict__
            ).dict()
            for watchlist in watchlists
        ]
        return CustomResponse.success(message="Watchlists Listings fetched", data=data)

    @openapi.definition(
        body=ReqBody(AddOrRemoveWatchlistSchema),
        summary="Add or Remove listing from a users watchlist",
        description="This endpoint adds or removes a listing from a user's watchlist, authenticated or not.",
        response=ResBody(ResponseSchema),
    )
    @openapi.secured("token", "guest")
    @validate_request(AddOrRemoveWatchlistSchema)
    async def post(self, request, db: AsyncSession, client: Client, **kwargs):
        data = kwargs["data"]
        client_id = client.id
        slug = data["slug"]

        listing = await listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        data_entry = {"session_key": client_id, "listing_id": listing.id}
        if client.is_authenticated:
            # Here we know its an auth user and not a guest, now we can retrieve id.
            del data_entry["session_key"]
            data_entry["user_id"] = client_id

        watchlist = await watchlist_manager.get_by_client_id_and_listing_id(
            db, client_id, listing.id
        )

        resp_message = "Listing removed from user watchlist"
        status_code = 200
        if not watchlist:
            await watchlist_manager.create(db, data_entry)
            resp_message = "Listing added to user watchlist"
            status_code = 201
        else:
            await watchlist_manager.delete(db, watchlist)

        guestuser_id = client_id if not client.is_authenticated else None
        return CustomResponse.success(
            message=resp_message,
            data={"guestuser_id": guestuser_id},
            status_code=status_code,
        )


class CategoryListView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all categories",
        description="This endpoint retrieves all categories",
        response=ResBody(CategoriesResponseSchema),
    )
    @openapi.secured("token", "guest")
    async def get(self, request, db: AsyncSession, **kwargs):
        categories = await category_manager.get_all(db)
        data = [CategoryDataSchema.from_orm(category).dict() for category in categories]
        return CustomResponse.success(message="Categories fetched", data=data)


class ListingsByCategoryView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all listings by category",
        description="This endpoint retrieves all listings in a particular category. Use slug 'other' for category other",
        response=ResBody(ListingsResponseSchema),
    )
    @openapi.secured("token", "guest")
    async def get(self, request, db: AsyncSession, client: Client, **kwargs):
        slug = kwargs.get("slug")
        # listings with category 'other' have category column as null
        category = None
        if slug != "other":
            category = await category_manager.get_by_slug(db, slug)
            if not category:
                return CustomResponse.error("Invalid category", status_code=404)

        listings = await listing_manager.get_by_category(db, category)
        data = [
            ListingDataSchema(
                watchlist=True
                if await watchlist_manager.get_by_client_id_and_listing_id(
                    db, client.id, listing.id
                )
                else False,
                time_left_seconds=listing.time_left_seconds,
                **listing.__dict__
            ).dict()
            for listing in listings
        ]
        return CustomResponse.success(message="Category Listings fetched", data=data)


class BidsView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve bids in a listing",
        description="This endpoint retrieves at most 3 bids from a particular listing.",
        response=ResBody(BidsResponseSchema),
    )
    @openapi.secured("token", "guest")
    async def get(self, request, db: AsyncSession, **kwargs):
        slug = kwargs["slug"]
        listing = await listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        bids = (await bid_manager.get_by_listing_id(db, listing.id))[:3]

        data = BidsResponseDataSchema(
            listing=listing.name,
            bids=[BidDataSchema.from_orm(bid) for bid in bids],
        ).dict()
        return CustomResponse.success(message="Listing Bids fetched", data=data)

    @openapi.definition(
        body=ReqBody(CreateBidSchema),
        summary="Add a bid to a listing",
        description="This endpoint adds a bid to a particular listing.",
        response=ResBody(BidResponseSchema),
        secured="token",
    )
    @validate_request(CreateBidSchema)
    async def post(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        slug = kwargs.get("slug")
        data = kwargs.get("data")

        listing = await listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        amount = data["amount"]
        bids_count = listing.bids_count
        if user.id == listing.auctioneer_id:
            return CustomResponse.error(
                "You cannot bid your own product!", status_code=403
            )
        elif not listing.active:
            return CustomResponse.error("This auction is closed!", status_code=410)
        elif listing.time_left < 1:
            return CustomResponse.error(
                "This auction is expired and closed!", status_code=410
            )
        elif amount < listing.price:
            return CustomResponse.error(
                "Bid amount cannot be less than the bidding price!"
            )
        elif amount <= listing.highest_bid:
            return CustomResponse.error("Bid amount must be more than the highest bid!")

        bid = await bid_manager.get_by_user_and_listing_id(db, user.id, listing.id)
        if bid:
            bid = await bid_manager.update(db, bid, {"amount": amount})
        else:
            bids_count += 1
            bid = await bid_manager.create(
                db,
                {"user_id": user.id, "listing_id": listing.id, "amount": amount},
            )

        # Update bids count and highest bids
        await listing_manager.update(
            db, listing, {"highest_bid": amount, "bids_count": bids_count}
        )
        data = BidDataSchema.from_orm(bid).dict()
        return CustomResponse.success(
            message="Bid added to listing", data=data, status_code=201
        )


listings_router.add_route(ListingsView.as_view(), "/")
listings_router.add_route(ListingDetailView.as_view(), "/detail/<slug>")
listings_router.add_route(ListingsByWatchListView.as_view(), "/watchlist")
listings_router.add_route(CategoryListView.as_view(), "/categories")
listings_router.add_route(ListingsByCategoryView.as_view(), "/categories/<slug>")
listings_router.add_route(BidsView.as_view(), "/detail/<slug>/bids")
