from sanic.response import json
from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import RequestBody, Response
from sanic_pydantic import webargs
from app.api.schemas.auth import RegisterUserSchema, LoginUserSchema
from app.db.models.accounts import User

auth_router = Blueprint("auth", url_prefix="/api/v2/auth")


class RegisterView(HTTPMethodView):
    decorators = [webargs(body=RegisterUserSchema)]

    @openapi.definition(
        body=RequestBody(RegisterUserSchema, required=True),
        summary="Register a new user",
        description="This endpoint registers new users into our application",
        # operation=
        # response=[Success, Response(Failure, status=400)],
    )
    async def post(self, request, body: RegisterUserSchema):
        data = body
        print(data)
        return json(data)


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


auth_router.add_route(RegisterView.as_view(), "/register", error_format="json")
auth_router.add_route(LoginView.as_view(), "/login")
