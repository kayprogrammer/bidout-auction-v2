from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.deps import AuthUser

from app.api.schemas.listings import (
    ListingDataSchema,
    ListingsResponseSchema,
    BidDataSchema,
    BidsResponseDataSchema,
    BidsResponseSchema,
)

from app.api.schemas.auctioneer import (
    CreateListingSchema,
    UpdateListingSchema,
    CreateListingResponseSchema,
    CreateListingResponseDataSchema,
    UpdateProfileSchema,
    UpdateProfileResponseDataSchema,
    UpdateProfileResponseSchema,
    ProfileDataSchema,
    ProfileResponseSchema,
)
from app.api.utils.responses import ReqBody, ResBody
from app.common.responses import CustomResponse
from app.db.managers.listings import (
    category_manager,
    listing_manager,
    bid_manager,
)
from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.api.utils.decorators import validate_request
from app.api.utils.validators import validate_quantity

auctioneer_router = Blueprint("Auctioneer", url_prefix="/api/v2/auctioneer")


class AuctioneerListingsView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all listings by the current user",
        description="This endpoint retrieves all listings by the current user",
        response=ResBody(ListingsResponseSchema),
        parameter={"name": "quantity", "location": "query", "schema": str},
        secured="token",
    )
    async def get(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        quantity = validate_quantity(request.args.get("quantity"))
        listings = await listing_manager.get_by_auctioneer_id(db, user.id)

        if quantity:
            # Retrieve based on amount
            listings = listings[:quantity]
        data = [ListingDataSchema.from_orm(listing).dict() for listing in listings]
        return CustomResponse.success(message="Auctioneer Listings fetched", data=data)

    @openapi.definition(
        body=ReqBody(CreateListingSchema),
        summary="Create a listing",
        description="This endpoint creates a new listing. Note: Use the returned upload_url to upload image to cloudinary",
        response=ResBody(CreateListingResponseSchema, status=201),
        secured="token",
    )
    @validate_request(CreateListingSchema)
    async def post(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        data = kwargs.get("data")
        category = data.get("category")

        if not category == "other":
            category = await category_manager.get_by_slug(db, category)
            if not category:
                # Return a data validation error
                return CustomResponse.error(
                    message="Invalid entry",
                    data={"category": "Invalid category"},
                    status_code=422,
                )
        else:
            category = None

        data.update(
            {
                "auctioneer_id": user.id,
                "category_id": category.id if category else None,
            }
        )
        data.pop("category", None)

        # Create file object
        file = await file_manager.create(db, {"resource_type": data["file_type"]})
        data.update({"image_id": file.id})
        data.pop("file_type")

        listing = await listing_manager.create(db, data)
        data = CreateListingResponseDataSchema.from_orm(listing).dict()
        return CustomResponse.success(
            message="Listing created successfully", data=data, status_code=201
        )


class UpdateListingView(HTTPMethodView):
    @openapi.definition(
        body=ReqBody(UpdateListingSchema),
        summary="Update a listing",
        description="This endpoint update a particular listing.",
        response=ResBody(CreateListingResponseSchema),
        secured="token",
    )
    @validate_request(UpdateListingSchema)
    async def patch(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        data = kwargs.get("data")
        slug = kwargs.get("slug")
        category = data.get("category")

        listing = await listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        if user.id != listing.auctioneer_id:
            return CustomResponse.error("This listing doesn't belong to you!")

        # Remove keys with values of None
        data = {k: v for k, v in data.items() if v not in (None, "")}

        if category:
            if not category == "other":
                category = await category_manager.get_by_slug(db, category)
                if not category:
                    # Return a data validation error
                    return CustomResponse.error(
                        message="Invalid entry",
                        data={"category": "Invalid category"},
                        status_code=422,
                    )
            else:
                category = None

            data.update({"category_id": category.id if category else None})
            data.pop("category", None)

        file_type = data.get("file_type")
        if file_type:
            await file_manager.delete(db, listing.image)
            # Create file object
            file = await file_manager.create(db, {"resource_type": file_type})
            data.update({"image_id": file.id})
        data.pop("file_type", None)

        listing = await listing_manager.update(db, listing, data)
        data = CreateListingResponseDataSchema.from_orm(listing).dict()
        return CustomResponse.success(message="Listing updated successfully", data=data)


class AuctioneerListingBidsView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve all bids in a listing (current user)",
        description="This endpoint retrieves all bids in a particular listing by the current user.",
        response=ResBody(BidsResponseSchema),
        secured="token",
    )
    async def get(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        slug = kwargs.get("slug")

        # Get listing by slug
        listing = await listing_manager.get_by_slug(db, slug)
        if not listing:
            return CustomResponse.error("Listing does not exist!", status_code=404)

        # Ensure the current user is the listing's owner
        if user.id != listing.auctioneer_id:
            return CustomResponse.error("This listing doesn't belong to you!")

        bids = await bid_manager.get_by_listing_id(db, listing.id)
        data = BidsResponseDataSchema(
            listing=listing.name,
            bids=[BidDataSchema.from_orm(bid) for bid in bids],
        ).dict()
        return CustomResponse.success(message="Listing Bids fetched", data=data)


class ProfileView(HTTPMethodView):
    @openapi.definition(
        summary="Get Profile",
        description="This endpoint gets the current user's profile.",
        response=ResBody(ProfileResponseSchema),
        secured="token",
    )
    async def get(self, request, user: AuthUser):
        data = ProfileDataSchema.from_orm(user).dict()
        return CustomResponse.success(message="User details fetched!", data=data)

    @openapi.definition(
        body=ReqBody(UpdateProfileSchema),
        summary="Update Profile",
        description="This endpoint updates an authenticated user's profile. Note: use the returned upload_url to upload avatar to cloudinary",
        response=ResBody(UpdateProfileResponseSchema),
        secured="token",
    )
    @validate_request(UpdateProfileSchema)
    async def put(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        data = kwargs["data"]

        file_type = data.get("file_type")
        if file_type:
            # Create file object
            file = await file_manager.create(db, {"resource_type": file_type})
            data.update({"avatar_id": file.id})
        data.pop("file_type", None)

        user = await user_manager.update(db, user, data)
        data = UpdateProfileResponseDataSchema.from_orm(user).dict()
        return CustomResponse.success(message="User updated!", data=data)


auctioneer_router.add_route(AuctioneerListingsView.as_view(), "/listings")
auctioneer_router.add_route(UpdateListingView.as_view(), "/listings/<slug>")
auctioneer_router.add_route(
    AuctioneerListingBidsView.as_view(), "/listings/<slug>/bids"
)
auctioneer_router.add_route(ProfileView.as_view(), "/")
