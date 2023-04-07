from sanic.response import json
from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.auth import RegisterUserSchema, LoginUserSchema
from app.api.schemas.base import ResponseSchema
from app.db.models.accounts import User
from app.common.responses import CustomResponse
from app.db.managers.accounts import user_manager

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
        user_manager.create(db, data)
        return CustomResponse.success(
            message="Registration successful", status_code=201
        )


class LoginView(HTTPMethodView):
    decorators = [webargs(body=LoginUserSchema)]

    @openapi.definition(
        body=RequestBody(LoginUserSchema, required=True),
        summary="Login a user",
        description="This endpoint generates new access and refresh tokens for a user",
    )
    async def post(self, request):
        print(request)
        return json({"my": "blueprint"})


auth_router.add_route(RegisterView.as_view(), "/register")
auth_router.add_route(LoginView.as_view(), "/login")
