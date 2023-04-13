from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.listings import (
    ListingDataSchema,
    ListingResponseSchema,
    ListingsResponseSchema,
    ListingQuerySchema,
    BidDataSchema,
    BidsResponseSchema,
)

from app.api.schemas.auctioneer import (
    CreateListingSchema,
    CreateListingResponseSchema,
    CreateListingResponseDataSchema,
    UpdateProfileSchema,
    UpdateProfileResponseDataSchema,
    UpdateProfileResponseSchema,
    ProfileDataSchema,
    ProfileResponseSchema,
)
from app.common.responses import CustomResponse
from app.db.managers.listings import (
    category_manager,
    listing_manager,
    bid_manager,
)
from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.api.utils.decorators import authorized

auctioneer_router = Blueprint("Auctioneer", url_prefix="/api/v2/auctioneer")


class AuctioneerListingsView(HTTPMethodView):
    decorators = [
        authorized(),
        webargs(query=ListingQuerySchema, body=CreateListingSchema),
    ]

    @openapi.definition(
        summary="Retrieve all listings by the current user",
        description="This endpoint retrieves all listings by the current user",
        response=Response(ListingsResponseSchema),
        parameter={"name": "quantity", "location": "query", "schema": int},
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        user = request.ctx.user
        quantity = request.args.get("quantity")
        quantity = int(quantity) if quantity else None
        listings = listing_manager.get_by_auctioneer_id(db, user.id)

        if quantity:
            # Retrieve based on amount
            listings = listings[:quantity]
        data = [ListingDataSchema.from_orm(listing).dict() for listing in listings]
        return CustomResponse.success(message="Auctioneer Listings fetched", data=data)

    @openapi.definition(
        body=CreateListingSchema,
        summary="Create a listing",
        description="This endpoint creates a new listing. Note: Use the returned upload_url to upload image to cloudinary",
        response=Response(CreateListingResponseSchema),
    )
    async def post(self, request, **kwargs):
        data = request.json
        db = request.ctx.db
        user = request.ctx.user
        category = data.get("category")

        if category:
            category = category_manager.get_by_slug(db, category)
            if not category:
                # Return a data validation error
                return CustomResponse.error(
                    message="Invalid entry",
                    data={"category": "Invalid category"},
                    status_code=422,
                )

        data.update(
            {"auctioneer_id": user.id, "category_id": category.id if category else None}
        )
        data.pop("category", None)

        # Create file object
        file = file_manager.create(db, {"resource_type": data["file_type"]})
        data.update({"image_id": file.id})
        data.pop("file_type")

        listing = listing_manager.create(db, data)
        data = CreateListingResponseDataSchema.from_orm(listing).dict()
        print(data)
        return CustomResponse.success(
            message="Listing created successfully", status_code=201
        )


class UpdateListingView(HTTPMethodView):
    decorators = [authorized()]

    @openapi.definition(
        body=RequestBody(CreateListingSchema, required=True),
        summary="Update a listing",
        description="This endpoint update a particular listing.",
        response=Response(CreateListingResponseSchema),
    )
    async def put(self, request, **kwargs):
        data = request.json
        db = request.ctx.db
        user = request.ctx.user
        slug = kwargs.get("slug")
        category = data.get("category")

        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        if user.id != listing.auctioneer_id:
            return CustomResponse.error("This listing doesn't belong to you!")

        if category:
            category = category_manager.get_by_slug(db, category)
            if not category:
                # Return a data validation error
                return CustomResponse.error(
                    message="Invalid entry",
                    data={"category": "Invalid category"},
                    status_code=422,
                )

        data.update({"category_id": category.id if category else None})
        data.pop("category", None)

        # Create file object
        file_manager.delete(db, listing.image)
        file = file_manager.create(db, {"resource_type": data["file_type"]})
        data.update({"image_id": file.id})
        data.pop("file_type")

        listing = listing_manager.update(db, listing, data)
        data = CreateListingResponseDataSchema.from_orm(listing).dict()
        return CustomResponse.success(
            message="Listing created successfully", data=data, status_code=201
        )


class AuctioneerListingBidsView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all bids in a listing (current user)",
        description="This endpoint retrieves all bids in a particular listing by the current user.",
        response=Response(BidsResponseSchema),
    )
    async def get(self, request, **kwargs):
        slug = kwargs.get("slug")
        db = request.ctx.db
        user = request.ctx.user

        # Get listing by slug
        listing = listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        # Ensure the current user is the listing's owner
        if user.id != listing.auctioneer_id:
            return CustomResponse.error("This listing doesn't belong to you!")

        bids = bid_manager.get_by_listing_id(db, listing.id)
        data = [BidDataSchema.from_orm(bid).dict() for bid in bids]
        return CustomResponse.success(message="Listing Bids fetched", data=data)


class ProfileView(HTTPMethodView):
    decorators = [authorized()]

    @openapi.definition(
        summary="Get Profile",
        description="This endpoint gets the current user's profile.",
        response=Response(ProfileResponseSchema),
    )
    async def get(self, request, **kwargs):
        data = request.json
        user = request.ctx.user

        data = ProfileDataSchema.from_orm(user).dict()
        return CustomResponse.success(message="User details fetched!", data=data)

    @openapi.definition(
        body=RequestBody(UpdateProfileSchema, required=True),
        summary="Update Profile",
        description="This endpoint updates an authenticated user's profile. Note: use the returned upload_url to upload avatar to cloudinary",
        response=Response(UpdateProfileResponseSchema),
    )
    async def put(self, request, **kwargs):
        data = request.json
        db = request.ctx.db
        user = request.ctx.user

        # Create file object
        file = file_manager.create(db, {"resource_type": data["file_type"]})
        data.pop("file_type")
        data.update({"avatar_id": file.id})

        user = user_manager.update(db, user, data)
        data = UpdateProfileResponseDataSchema.from_orm(user).dict()
        return CustomResponse.success(message="User updated!", data=data)


auctioneer_router.add_route(AuctioneerListingsView.as_view(), "/listings")
auctioneer_router.add_route(UpdateListingView.as_view(), "/listings/<slug>")
auctioneer_router.add_route(
    AuctioneerListingBidsView.as_view(), "/listings/<slug>/bids"
)
auctioneer_router.add_route(ProfileView.as_view(), "/")
