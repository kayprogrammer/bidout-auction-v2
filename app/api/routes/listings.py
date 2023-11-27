from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody
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
from app.common.responses import CustomResponse
from app.db.managers.listings import (
    listing_manager,
    bid_manager,
    watchlist_manager,
    category_manager,
)
from app.api.utils.decorators import authorized, validate_request
from app.api.utils.validators import validate_quantity

listings_router = Blueprint("Listings", url_prefix="/api/v2/listings")


class ListingsView(HTTPMethodView):
    decorators = [authorized()]

    @openapi.definition(
        summary="Retrieve all listings",
        description="This endpoint retrieves all listings",
        response={"application/json": ListingsResponseSchema},
        parameter={"name": "quantity", "location": "query", "schema": int},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, **kwargs):
        db = request.ctx.db
        client_id = request.ctx.user.id

        quantity = validate_quantity(request.args.get("quantity"))
        listings = listing_manager.get_all(db)
        if quantity:
            # Retrieve based on amount
            listings = listings[:quantity]

        data = [
            ListingDataSchema(
                watchlist=True
                if watchlist_manager.get_by_user_id_or_session_key_and_listing_id(
                    db, client_id, listing.id
                )
                else False,
                bids_count=listing.bids_count,
                highest_bid=listing.highest_bid,
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
        response={"application/json": ListingResponseSchema},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, **kwargs):
        slug = kwargs.get("slug")
        db = request.ctx.db
        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        related_listings = listing_manager.get_related_listings(
            db, listing.category_id, slug
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
    decorators = [authorized()]

    @openapi.definition(
        summary="Retrieve all listings by users watchlist",
        description="This endpoint retrieves all listings",
        response={"application/json": ListingsResponseSchema},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, **kwargs):
        db = request.ctx.db
        client_id = request.ctx.user.id

        watchlists = watchlist_manager.get_by_user_id_or_session_key(db, client_id)
        data = [
            ListingDataSchema(
                watchlist=True,
                bids_count=watchlist.listing.bids_count,
                highest_bid=watchlist.listing.highest_bid,
                time_left_seconds=watchlist.listing.time_left_seconds,
                **watchlist.listing.__dict__
            ).dict()
            for watchlist in watchlists
        ]
        return CustomResponse.success(message="Watchlists Listings fetched", data=data)

    @openapi.definition(
        body=RequestBody(
            {"application/json": AddOrRemoveWatchlistSchema}, required=True
        ),
        summary="Add or Remove listing from a users watchlist",
        description="This endpoint adds or removes a listing from a user's watchlist, authenticated or not.",
        response={"application/json": ResponseSchema},
    )
    @openapi.secured("token", "guest")
    @validate_request(AddOrRemoveWatchlistSchema)
    async def post(self, request, **kwargs):
        data = kwargs["data"]
        db = request.ctx.db
        user = request.ctx.user
        client_id = user.id
        slug = data["slug"]

        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        data_entry = {"session_key": client_id, "listing_id": listing.id}
        if user.is_authenticated:
            # Here we know its an auth user and not a guest, now we can retrieve id.
            del data_entry["session_key"]
            data_entry["user_id"] = client_id

        watchlist = watchlist_manager.get_by_user_id_or_session_key_and_listing_id(
            db, client_id, listing.id
        )

        resp_message = "Listing removed from user watchlist"
        status_code = 200
        if not watchlist:
            watchlist_manager.create(db, data_entry)
            resp_message = "Listing added to user watchlist"
            status_code = 201
        else:
            watchlist_manager.delete(db, watchlist)

        guestuser_id = client_id if not user.is_authenticated else None
        return CustomResponse.success(
            message=resp_message,
            data={"guestuser_id": guestuser_id},
            status_code=status_code,
        )


class CategoryListView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all categories",
        description="This endpoint retrieves all categories",
        response={"application/json": CategoriesResponseSchema},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, **kwargs):
        db = request.ctx.db
        categories = category_manager.get_all(db)
        data = [CategoryDataSchema.from_orm(category).dict() for category in categories]
        return CustomResponse.success(message="Categories fetched", data=data)


class ListingsByCategoryView(HTTPMethodView):
    decorators = [authorized()]

    @openapi.definition(
        summary="Retrieve all listings by category",
        description="This endpoint retrieves all listings in a particular category. Use slug 'other' for category other",
        response={"application/json": ListingsResponseSchema},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, **kwargs):
        db = request.ctx.db
        slug = kwargs.get("slug")
        # listings with category 'other' have category column as null
        category = None
        if slug != "other":
            category = category_manager.get_by_slug(db, slug)
            if not category:
                return CustomResponse.error("Invalid category", status_code=404)

        client_id = request.ctx.user.id

        listings = listing_manager.get_by_category(db, category)
        data = [
            ListingDataSchema(
                watchlist=True
                if watchlist_manager.get_by_user_id_or_session_key_and_listing_id(
                    db, client_id, listing.id
                )
                else False,
                bids_count=listing.bids_count,
                highest_bid=listing.highest_bid,
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
        response={"application/json": BidsResponseSchema},
    )
    @openapi.secured("token", "guest")
    async def get(self, request, **kwargs):
        slug = kwargs.get("slug")
        db = request.ctx.db
        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        bids = bid_manager.get_by_listing_id(db, listing.id)[:3]

        data = BidsResponseDataSchema(
            listing=listing.name,
            bids=[BidDataSchema.from_orm(bid) for bid in bids],
        ).dict()
        return CustomResponse.success(message="Listing Bids fetched", data=data)

    @openapi.definition(
        body=RequestBody({"application/json": CreateBidSchema}, required=True),
        summary="Add a bid to a listing",
        description="This endpoint adds a bid to a particular listing.",
        response={"application/json": BidResponseSchema},
    )
    @authorized()
    @validate_request(CreateBidSchema)
    @openapi.secured("token")
    async def post(self, request, **kwargs):
        slug = kwargs.get("slug")
        data = kwargs.get("data")
        db = request.ctx.db
        user = request.ctx.user

        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        amount = data["amount"]
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

        bid = bid_manager.get_by_user_and_listing_id(db, user.id, listing.id)
        if bid:
            bid = bid_manager.update(db, bid, {"amount": amount})
        else:
            bid = bid_manager.create(
                db,
                {"user_id": user.id, "listing_id": listing.id, "amount": amount},
            )

        data = BidDataSchema.from_orm(bid).dict()
        return CustomResponse.success(
            message="Bid added to listing", data=data, status_code=201
        )


# listings_router.add_route(ListingsView.as_view(), "/")
# listings_router.add_route(ListingDetailView.as_view(), "/detail/<slug>")
# listings_router.add_route(ListingsByWatchListView.as_view(), "/watchlist")
# listings_router.add_route(CategoryListView.as_view(), "/categories")
# listings_router.add_route(ListingsByCategoryView.as_view(), "/categories/<slug>")
# listings_router.add_route(BidsView.as_view(), "/detail/<slug>/bids")
