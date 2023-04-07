from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.auth import (
    RegisterUserSchema,
    VerifyEmailSchema,
    ResendVerificationEmailSchema,
    LoginUserSchema,
)
from app.api.schemas.base import ResponseSchema
from app.db.models.accounts import User
from app.common.responses import CustomResponse
from app.db.managers.accounts import user_manager, otp_manager
from app.api.utils.emails import send_email

auth_router = Blueprint("auth", url_prefix="/api/v2/auth")


class RegisterView(HTTPMethodView):
    decorators = [webargs(body=RegisterUserSchema)]

    @openapi.definition(
        body=RequestBody(RegisterUserSchema, required=True),
        summary="Register a new user",
        description="This endpoint registers new users into our application",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.session
        data = request.json
        user = user_manager.create(db, data)

        # Send verification email
        send_email(request, db, user, "activate")

        return CustomResponse.success(
            message="Registration successful", status_code=201
        )


class VerifyEmailView(HTTPMethodView):
    decorators = [webargs(body=VerifyEmailSchema)]

    @openapi.definition(
        body=RequestBody(VerifyEmailSchema, required=True),
        summary="Verify a user's email",
        description="This endpoint verifies a user's email",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.session
        data = request.json
        user_by_email = user_manager.get_by_email(db, data["email"])

        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)
        if user_by_email.is_email_verified:
            return CustomResponse.success("Email already verified", status_code=200)

        otp = otp_manager.get_by_user_id(db, user_by_email.id)
        if not otp or otp.code != data["code"]:
            return CustomResponse.error("Incorrect Otp", status_code=400)
        if otp.check_expiration():
            return CustomResponse.error("Expired Otp", status_code=400)

        user = user_manager.update(db, user_by_email, {"is_email_verified": True})
        otp_manager.delete(db, otp)

        # Send welcome email
        send_email(request, db, user, "welcome")
        return CustomResponse.success(
            message="Account verification successful", status_code=200
        )


class ResendVerificationEmailView(HTTPMethodView):
    decorators = [webargs(body=ResendVerificationEmailSchema)]

    @openapi.definition(
        body=RequestBody(ResendVerificationEmailSchema, required=True),
        summary="Resend Verification Email",
        description="This endpoint resends new otp to the user's email",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.session
        data = request.json
        user_by_email = user_manager.get_by_email(db, data["email"])
        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)
        if user_by_email.is_email_verified:
            return CustomResponse.success("Email already verified", status_code=200)

        # Send verification email
        send_email(request, db, user_by_email, "activate")

        return CustomResponse.success(
            message="Verification email sent", status_code=200
        )


auth_router.add_route(RegisterView.as_view(), "/register")
auth_router.add_route(VerifyEmailView.as_view(), "/verify-email")
auth_router.add_route(
    ResendVerificationEmailView.as_view(), "/resend-verification-email"
)
