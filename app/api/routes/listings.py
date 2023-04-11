from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.listings import (
    CreateBidSchema,
    CreateWatchlistSchema,
    ListingDataSchema,
    ListingsResponseSchema,
    ListListingsResponseSchema,
    ListingsQuerySchema,
)
from app.common.responses import CustomResponse
from app.db.managers.listings import (
    listing_manager,
    bid_manager,
    watchlist_manager,
    category_manager,
)
from app.api.utils.decorators import authorized

listings_router = Blueprint("listings", url_prefix="/api/v2/listings")


class ListingsView(HTTPMethodView):
    decorators = [webargs(query=ListingsQuerySchema)]

    @openapi.definition(
        summary="Retrieve all listings",
        description="This endpoint retrieves all listings",
        response=Response(ListListingsResponseSchema),
        parameter={"name": "quantity", "location": "query", "schema": int},
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        quantity = request.args.get("quantity")
        quantity = int(quantity) if quantity else None
        listings = listing_manager.get_all(db)
        if quantity:
            listings = listings[:quantity]
        data = [ListingDataSchema.from_orm(listing).dict() for listing in listings]
        return CustomResponse.success(message="Listings fetched", data=data)


class ListingDetailView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve listing's detail",
        description="This endpoint retrieves detail of a listing",
        response=Response(ListingsResponseSchema),
    )
    async def get(self, request, **kwargs):
        slug = kwargs.get("slug")
        db = request.ctx.db
        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        data = ListingDataSchema.from_orm(listing).dict()
        return CustomResponse.success(message="Listings fetched", data=data)


class ListingsByWatchListView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all listings by users watchlist",
        description="This endpoint retrieves all listings",
        response=Response(ListingsResponseSchema),
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        user = request.ctx.user
        watchlists = watchlist_manager.get_by_user_id_or_session_key(db, user)
        data = [
            ListingDataSchema.from_orm(watchlist.listing).dict()
            for watchlist in watchlists
        ]
        return CustomResponse.success(message="Watchlists Listings fetched", data=data)

    @openapi.definition(
        body=RequestBody(CreateWatchlistSchema, required=True),
        summary="Add a listing to a users watchlist",
        description="This endpoint adds a listing to a user's watchlist, authenticated or not.",
        response=Response(ListingsResponseSchema),
    )
    async def post(self, request, **kwargs):
        data = request.json
        db = request.ctx.db
        user = request.ctx.user

        listing = listing_manager.get_by_slug(db, data.get("slug"))
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        data_entry = {"session_key": user, "listing_id": listing.id}
        if hasattr(user, "email"):
            data_entry["user_id"] = user.id
            del data_entry["session_key"]

        watchlist = watchlist_manager.create(db, data_entry)
        data = ListingDataSchema.from_orm(watchlist.listing).dict()
        return CustomResponse.success(message="Listing added to Watchlists", data=data)


class ListingsByCategoryView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all listings by category",
        description="This endpoint retrieves all listings in a particular category. Use slug 'other' for category other",
        response=Response(ListingsResponseSchema),
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        slug = kwargs.get("slug")
        category = None
        if slug != "other":
            category = category_manager.get_by_slug(db, slug)
            if not category:
                return CustomResponse.error("Invalid category", status_code=404)

        listings = listing_manager.get_by_category(db, category)
        data = [ListingDataSchema.from_orm(listing).dict() for listing in listings]
        return CustomResponse.success(message="Category Listings fetched", data=data)


listings_router.add_route(ListingsView.as_view(), "/")
listings_router.add_route(ListingDetailView.as_view(), "/<slug>")
listings_router.add_route(ListingsByWatchListView.as_view(), "/watchlist")
listings_router.add_route(ListingsByCategoryView.as_view(), "/category/<slug>")
