from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.auth import (
    RegisterUserSchema,
    VerifyOtpSchema,
    RequestOtpSchema,
    SetNewPasswordSchema,
    LoginUserSchema,
    RefreshTokensSchema,
)
from app.api.schemas.base import ResponseSchema
from app.db.models.accounts import User
from app.common.responses import CustomResponse
from app.db.managers.accounts import user_manager, otp_manager, jwt_manager
from app.api.utils.emails import send_email
from app.core.security import verify_password
from app.api.utils.tokens import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.api.utils.decorators import authorized

auth_router = Blueprint("Auth", url_prefix="/api/v2/auth")


class RegisterView(HTTPMethodView):
    decorators = [webargs(body=RegisterUserSchema)]

    @openapi.definition(
        body=RequestBody(RegisterUserSchema, required=True),
        summary="Register a new user",
        description="This endpoint registers new users into our application",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        data = request.json
        user = user_manager.create(db, data)

        # Send verification email
        send_email(request, db, user, "activate")

        return CustomResponse.success(
            message="Registration successful", status_code=201
        )


class VerifyEmailView(HTTPMethodView):
    decorators = [webargs(body=VerifyOtpSchema)]

    @openapi.definition(
        body=RequestBody(VerifyOtpSchema, required=True),
        summary="Verify a user's email",
        description="This endpoint verifies a user's email",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        data = request.json
        user_by_email = user_manager.get_by_email(db, data["email"])

        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)
        if user_by_email.is_email_verified:
            return CustomResponse.success("Email already verified", status_code=200)

        otp = otp_manager.get_by_user_id(db, user_by_email.id)
        if not otp or otp.code != data["otp"]:
            return CustomResponse.error("Incorrect Otp")
        if otp.check_expiration():
            return CustomResponse.error("Expired Otp")

        user = user_manager.update(db, user_by_email, {"is_email_verified": True})
        otp_manager.delete(db, otp)

        # Send welcome email
        send_email(request, db, user, "welcome")
        return CustomResponse.success(
            message="Account verification successful", status_code=200
        )


class ResendVerificationEmailView(HTTPMethodView):
    decorators = [webargs(body=RequestOtpSchema)]

    @openapi.definition(
        body=RequestBody(RequestOtpSchema, required=True),
        summary="Resend Verification Email",
        description="This endpoint resends new otp to the user's email",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
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


class SendPasswordResetOtpView(HTTPMethodView):
    decorators = [webargs(body=RequestOtpSchema)]

    @openapi.definition(
        body=RequestBody(RequestOtpSchema, required=True),
        summary="Send Password Reset Otp",
        description="This endpoint sends new password reset otp to the user's email",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        data = request.json
        user_by_email = user_manager.get_by_email(db, data["email"])
        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)

        # Send password reset email
        send_email(request, db, user_by_email, "reset")

        return CustomResponse.success(message="Password otp sent", status_code=200)


class VerifyPasswordResetOtpView(HTTPMethodView):
    decorators = [webargs(body=VerifyOtpSchema)]

    @openapi.definition(
        body=RequestBody(VerifyOtpSchema, required=True),
        summary="Verify Password Reset Otp",
        description="This endpoint verifies the password reset otp",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        data = request.json
        user_by_email = user_manager.get_by_email(db, data["email"])
        if not user_by_email:
            return CustomResponse.error("Incorrect Email", status_code=404)

        otp = otp_manager.get_by_user_id(db, user_by_email.id)
        if not otp or otp.code != data["otp"]:
            return CustomResponse.error("Incorrect Otp")
        if otp.check_expiration():
            return CustomResponse.error("Expired Otp")

        response = CustomResponse.success(
            message="Otp verified successfully", status_code=200
        )
        response.add_cookie("email", user_by_email.email, max_age=900)
        return response


class SetNewPasswordView(HTTPMethodView):
    decorators = [webargs(body=SetNewPasswordSchema)]

    @openapi.definition(
        body=RequestBody(SetNewPasswordSchema, required=True),
        summary="Set New Password",
        description="This endpoint works only when the reset otp has been successfully verified within the same request",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        email = request.cookies.get("email")
        if not email:
            return CustomResponse.error("Reset otp is not verified yet!")
        password = request.json["password"]
        user_by_email = user_manager.get_by_email(db, email)
        if not user_by_email:
            return CustomResponse.error("Something went wrong", status_code=500)

        user_manager.update(db, user_by_email, {"password": password})

        # Send password reset success email
        send_email(request, db, user_by_email, "reset-success")

        response = CustomResponse.success(
            message="Password reset successfully", status_code=200
        )
        response.delete_cookie("email")
        return response


class LoginView(HTTPMethodView):
    decorators = [webargs(body=LoginUserSchema)]

    @openapi.definition(
        body=RequestBody(LoginUserSchema, required=True),
        summary="Login a user",
        description="This endpoint generates new access and refresh tokens for authentication",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        data = request.json
        email = data["email"]
        plain_password = data["password"]
        user = user_manager.get_by_email(db, email)
        if not user or verify_password(plain_password, user.password) == False:
            return CustomResponse.error("Invalid credentials", status_code=401)

        if not user.is_email_verified:
            return CustomResponse.error("Verify your email first", status_code=401)

        jwt_manager.delete_by_user_id(db, user.id)

        # Create tokens and store in jwt model
        access = create_access_token({"user_id": str(user.id)})
        refresh = create_refresh_token()
        jwt_manager.create(
            db, {"user_id": user.id, "access": access, "refresh": refresh}
        )

        return CustomResponse.success(
            message="Login successful",
            data={"access": access, "refresh": refresh},
            status_code=201,
        )


class RefreshTokensView(HTTPMethodView):
    decorators = [webargs(body=RefreshTokensSchema)]

    @openapi.definition(
        body=RequestBody(RefreshTokensSchema, required=True),
        summary="Refresh tokens",
        description="This endpoint refresh tokens by generating new access and refresh tokens for a user",
        response=Response(ResponseSchema),
    )
    async def post(self, request, **kwargs):
        db = request.ctx.db
        data = request.json
        token = data["refresh"]
        jwt = jwt_manager.get_by_refresh(db, token)
        if not jwt:
            return CustomResponse.error(
                "Refresh token does not exists", status_code=404
            )
        if not verify_refresh_token(token):
            return CustomResponse.error(
                "Refresh token is invalid or expired", status_code=401
            )

        access = create_access_token({"user_id": str(jwt.user_id)})
        refresh = create_refresh_token()

        jwt_manager.update(db, jwt, {"access": access, "refresh": refresh})

        return CustomResponse.success(
            message="Tokens refresh successful",
            data={"access": access, "refresh": refresh},
            status_code=200,
        )


class LogoutView(HTTPMethodView):
    decorators = [authorized()]

    @openapi.definition(
        summary="Logout a user",
        description="This endpoint logs a user out from our application",
        response=Response(ResponseSchema),
        operation="security",
    )
    async def get(self, request, **kwargs):
        db = request.ctx.db
        user = request.ctx.user
        jwt = jwt_manager.get_by_user_id(db, user.id)
        jwt_manager.delete(db, jwt)

        return CustomResponse.success(message="Logout successful")


auth_router.add_route(RegisterView.as_view(), "/register")
auth_router.add_route(VerifyEmailView.as_view(), "/verify-email")
auth_router.add_route(
    ResendVerificationEmailView.as_view(), "/resend-verification-email"
)
auth_router.add_route(SendPasswordResetOtpView.as_view(), "/request-password-reset-otp")
auth_router.add_route(
    VerifyPasswordResetOtpView.as_view(), "/verify-password-reset-otp"
)
auth_router.add_route(SetNewPasswordView.as_view(), "/set-new-password")
auth_router.add_route(LoginView.as_view(), "/login")
auth_router.add_route(RefreshTokensView.as_view(), "/refresh")
auth_router.add_route(LogoutView.as_view(), "/logout")
