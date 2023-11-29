from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.routes.deps import AuthUser, Client
from app.api.schemas.auth import (
    RegisterUserSchema,
    VerifyOtpSchema,
    RequestOtpSchema,
    SetNewPasswordSchema,
    LoginUserSchema,
    RefreshTokensSchema,
)
from app.api.schemas.base import ResponseSchema
from app.api.utils.responses import ReqBody, ResBody
from app.common.responses import CustomResponse
from app.db.managers.accounts import user_manager, otp_manager, jwt_manager
from app.db.managers.base import guestuser_manager
from app.db.managers.listings import watchlist_manager

from app.api.utils.emails import send_email
from app.core.security import verify_password
from app.api.utils.tokens import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.api.utils.decorators import validate_request
from app.db.models.base import GuestUser

auth_router = Blueprint("Auth", url_prefix="/api/v2/auth")


class RegisterView(HTTPMethodView):
    decorators = [validate_request(RegisterUserSchema)]

    @openapi.definition(
        body=ReqBody(RegisterUserSchema),
        summary="Register a new user",
        description="This endpoint registers new users into our application",
        response=ResBody(ResponseSchema, status=201),
    )
    async def post(self, request, db: AsyncSession, **kwargs):
        data = kwargs["data"]

        # Check for existing user
        existing_user = await user_manager.get_by_email(db, data["email"])
        if existing_user:
            return CustomResponse.error(
                "Invalid Entry",
                data={"email": "Email already registered!"},
                status_code=422,
            )

        # Create user
        user = await user_manager.create(db, data)

        # Send verification email
        await send_email(request, db, user, "activate")

        return CustomResponse.success(
            message="Registration successful",
            data={"email": user.email},
            status_code=201,
        )


class VerifyEmailView(HTTPMethodView):
    decorators = [validate_request(VerifyOtpSchema)]

    @openapi.definition(
        body=ReqBody(VerifyOtpSchema),
        summary="Verify a user's email",
        description="This endpoint verifies a user's email",
        response=ResBody(ResponseSchema),
    )
    async def post(self, request, db: AsyncSession, **kwargs):
        data = kwargs["data"]
        user_by_email = await user_manager.get_by_email(db, data["email"])

        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)
        if user_by_email.is_email_verified:
            return CustomResponse.success("Email already verified")

        otp = await otp_manager.get_by_user_id(db, user_by_email.id)
        if not otp or otp.code != data["otp"]:
            return CustomResponse.error("Incorrect Otp")
        if otp.check_expiration():
            return CustomResponse.error("Expired Otp")

        user = await user_manager.update(db, user_by_email, {"is_email_verified": True})
        await otp_manager.delete(db, otp)

        # Send welcome email
        await send_email(request, db, user, "welcome")
        return CustomResponse.success(message="Account verification successful")


class ResendVerificationEmailView(HTTPMethodView):
    decorators = [validate_request(RequestOtpSchema)]

    @openapi.definition(
        body=ReqBody(RequestOtpSchema),
        summary="Resend Verification Email",
        description="This endpoint resends new otp to the user's email",
        response=ResBody(ResponseSchema),
    )
    async def post(self, request, db: AsyncSession, **kwargs):
        data = kwargs["data"]
        user_by_email = await user_manager.get_by_email(db, data["email"])
        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)
        if user_by_email.is_email_verified:
            return CustomResponse.success("Email already verified")

        # Send verification email
        await send_email(request, db, user_by_email, "activate")

        return CustomResponse.success(message="Verification email sent")


class SendPasswordResetOtpView(HTTPMethodView):
    decorators = [validate_request(RequestOtpSchema)]

    @openapi.definition(
        body=ReqBody(RequestOtpSchema),
        summary="Send Password Reset Otp",
        description="This endpoint sends new password reset otp to the user's email",
        response=ResBody(ResponseSchema),
    )
    async def post(self, request, db: AsyncSession, **kwargs):
        data = kwargs["data"]
        user_by_email = await user_manager.get_by_email(db, data["email"])
        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)

        # Send password reset email
        await send_email(request, db, user_by_email, "reset")

        return CustomResponse.success(message="Password otp sent")


class SetNewPasswordView(HTTPMethodView):
    decorators = [validate_request(SetNewPasswordSchema)]

    @openapi.definition(
        body=ReqBody(SetNewPasswordSchema),
        summary="Set New Password",
        description="This endpoint verifies the password reset otp",
        response=ResBody(ResponseSchema),
    )
    async def post(self, request, db: AsyncSession, **kwargs):
        data = kwargs["data"]
        email = data["email"]
        otp_code = data["otp"]
        password = data["password"]

        user_by_email = await user_manager.get_by_email(db, email)
        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)

        otp = await otp_manager.get_by_user_id(db, user_by_email.id)
        if not otp or otp.code != otp_code:
            return CustomResponse.error("Incorrect Otp")
        if otp.check_expiration():
            return CustomResponse.error("Expired Otp")

        await user_manager.update(db, user_by_email, {"password": password})
        await otp_manager.delete(db, otp)

        # Send password reset success email
        await send_email(request, db, user_by_email, "reset-success")

        return CustomResponse.success(message="Password reset successful")


class LoginView(HTTPMethodView):
    decorators = [validate_request(LoginUserSchema)]

    @openapi.definition(
        body=ReqBody(LoginUserSchema),
        summary="Login a user",
        description="This endpoint generates new access and refresh tokens for authentication",
        response=ResBody(ResponseSchema, status=201),
    )
    @openapi.secured("guest")
    async def post(self, request, db: AsyncSession, client: Client, **kwargs):
        data = kwargs["data"]
        email = data["email"]
        plain_password = data["password"]
        user = await user_manager.get_by_email(db, email)
        if not user or verify_password(plain_password, user.password) == False:
            return CustomResponse.error("Invalid credentials", status_code=401)

        if not user.is_email_verified:
            return CustomResponse.error("Verify your email first", status_code=401)

        await jwt_manager.delete_by_user_id(db, user.id)

        # Create tokens and store in jwt model
        access = create_access_token({"user_id": str(user.id)})
        refresh = create_refresh_token()
        await jwt_manager.create(
            db, {"user_id": user.id, "access": access, "refresh": refresh}
        )

        # Move all guest user watchlists to the authenticated user watchlists
        guest_user_watchlists = await watchlist_manager.get_by_session_key(
            db, client.id if client else None, user.id
        )
        if len(guest_user_watchlists) > 0:
            data_to_create = [
                {"user_id": user.id, "listing_id": listing_id}.copy()
                for listing_id in guest_user_watchlists
            ]
            await watchlist_manager.bulk_create(db, data_to_create)

        if isinstance(client, GuestUser):
            # Delete client (Almost like clearing sessions)
            await guestuser_manager.delete(db, client)

        response = CustomResponse.success(
            message="Login successful",
            data={"access": access, "refresh": refresh},
            status_code=201,
        )
        return response


class RefreshTokensView(HTTPMethodView):
    decorators = [validate_request(RefreshTokensSchema)]

    @openapi.definition(
        body=ReqBody(RefreshTokensSchema),
        summary="Refresh tokens",
        description="This endpoint refresh tokens by generating new access and refresh tokens for a user",
        response=ResBody(ResponseSchema, status=201),
    )
    async def post(self, request, db: AsyncSession, **kwargs):
        data = kwargs["data"]
        token = data["refresh"]
        jwt = await jwt_manager.get_by_refresh(db, token)
        if not jwt:
            return CustomResponse.error("Refresh token does not exist", status_code=404)
        if not verify_refresh_token(token):
            return CustomResponse.error(
                "Refresh token is invalid or expired", status_code=401
            )

        access = create_access_token({"user_id": str(jwt.user_id)})
        refresh = create_refresh_token()

        await jwt_manager.update(db, jwt, {"access": access, "refresh": refresh})

        return CustomResponse.success(
            message="Tokens refresh successful",
            data={"access": access, "refresh": refresh},
            status_code=201,
        )


class LogoutView(HTTPMethodView):
    @openapi.definition(
        summary="Logout a user",
        description="This endpoint logs a user out from our application",
        response=ResBody(ResponseSchema),
        operation="security",
    )
    @openapi.secured("token")
    async def get(self, request, db: AsyncSession, user: AuthUser, **kwargs):
        jwt = await jwt_manager.get_by_user_id(db, user.id)
        await jwt_manager.delete(db, jwt)
        return CustomResponse.success(message="Logout successful")


auth_router.add_route(RegisterView.as_view(), "/register")
auth_router.add_route(VerifyEmailView.as_view(), "/verify-email")
auth_router.add_route(
    ResendVerificationEmailView.as_view(), "/resend-verification-email"
)
auth_router.add_route(SendPasswordResetOtpView.as_view(), "/request-password-reset-otp")
auth_router.add_route(SetNewPasswordView.as_view(), "/set-new-password")
auth_router.add_route(LoginView.as_view(), "/login")
auth_router.add_route(RefreshTokensView.as_view(), "/refresh")
auth_router.add_route(LogoutView.as_view(), "/logout")
