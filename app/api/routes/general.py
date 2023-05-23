from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody
from app.api.schemas.general import (
    SiteDetailDataSchema,
    SiteDetailResponseSchema,
    SubscriberSchema,
    SubscriberResponseSchema,
    ReviewsDataSchema,
    ReviewsResponseSchema,
)
from app.common.responses import CustomResponse
from app.db.managers.general import (
    sitedetail_manager,
    subscriber_manager,
    review_manager,
)
from app.api.utils.decorators import validate_request

general_router = Blueprint("General", url_prefix="/api/v2/general")


class SiteDetailView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve site details",
        description="This endpoint retrieves few details of the site/application",
        response={"application/json": SiteDetailResponseSchema},
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        sitedetail = sitedetail_manager.get(db)
        data = SiteDetailDataSchema.from_orm(sitedetail).dict()
        return CustomResponse.success(message="Site Details fetched", data=data)


class SubscriberCreateView(HTTPMethodView):
    @openapi.definition(
        body=RequestBody({"application/json": SubscriberSchema}, required=True),
        summary="Add a suscriber",
        description="This endpoint creates a suscriber in our application",
        response={"application/json": SubscriberResponseSchema},
    )
    @validate_request(SubscriberSchema)
    async def post(self, request, **kwargs):
        db = request.ctx.db
        email = request.json["email"]
        suscriber = subscriber_manager.get_by_email(db, email)
        if not suscriber:
            suscriber = subscriber_manager.create(db, {"email": email})

        data = SubscriberSchema.from_orm(suscriber).dict()
        return CustomResponse.success(
            message="Suscriber added successfully", data=data, status_code=201
        )


class ReviewsView(HTTPMethodView):
    @openapi.definition(
        summary="Retrieve site reviews",
        description="This endpoint retrieves a few reviews of the application",
        response={"application/json": ReviewsResponseSchema},
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        reviews = review_manager.get_active(db)[:3]
        data = [ReviewsDataSchema.from_orm(review).dict() for review in reviews]
        return CustomResponse.success(message="Reviews fetched", data=data)


general_router.add_route(SiteDetailView.as_view(), "/site-detail")
general_router.add_route(SubscriberCreateView.as_view(), "/subscribe")
general_router.add_route(ReviewsView.as_view(), "/reviews")
