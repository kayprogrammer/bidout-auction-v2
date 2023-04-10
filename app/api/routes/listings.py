from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.listings import (
    CreateListingSchema,
    CreateBidSchema,
    CreateWatchlistSchema,
    ListingDataSchema,
    ListingsResponseSchema,
)
from app.api.schemas.base import ResponseSchema
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
    @openapi.definition(
        summary="Retrieve all listings",
        description="This endpoint retrieves all listings",
        response=Response(ListingsResponseSchema),
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        listings = listing_manager.get_all(db)
        data = [ListingDataSchema.from_orm(listing).dict() for listing in listings]
        return CustomResponse.success(message="Listings fetched", data=data)


listings_router.add_route(ListingsView.as_view(), "/")
