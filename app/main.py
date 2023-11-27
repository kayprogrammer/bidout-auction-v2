from sanic import Sanic, Request
from sanic.response import json
from sanic_ext import Config, openapi
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from app.api.routes.auth import auth_router
from app.api.routes.listings import listings_router
from app.api.routes.auctioneer import auctioneer_router
from app.api.routes.general import general_router

from app.core.config import settings
from app.common.exception_handlers import (
    sanic_exceptions_handler,
    validation_exception_handler,
)
from app.common.middlewares import (
    add_cors_headers,
    inject_current_user,
)
from pydantic import ValidationError

from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader("app", "templates"))

app = Sanic(name=settings.PROJECT_NAME)

# SWAGGER DOCS CONFIG
app.extend(
    config=Config(
        oas_ui_default="swagger",
        oas_url_prefix="/",
    )
)
app.ext.openapi.describe(
    f"{settings.PROJECT_NAME} API",
    version="2",
    description="This is a simple Auction API",
)
app.ext.openapi.add_security_scheme(
    ident="guest", name="GuestUserId", type="apiKey", location="header"
)
app.ext.openapi.add_security_scheme(
    "token",
    "http",
    scheme="bearer",
    bearer_format="JWT",
)


# ---------------------------
# SETUP DATABASE
# ---------------------
def get_db(request: Request):
    return request.app.ctx.db_conn


@app.before_server_start
async def setup_db(app, _):
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    app.ctx.db_conn = SessionLocal()
    app.ext.add_dependency(AsyncSession, get_db)


# --------------------------
# REGISTER MIDDLEWARES
app.register_middleware(add_cors_headers, "response", priority=99)
# app.register_middleware(inject_current_user, "request")

# EXCEPTION HANDLERS
app.error_handler.add(Exception, sanic_exceptions_handler)
app.error_handler.add(ValidationError, validation_exception_handler)

# REGISTER BLUEPRINTS
app.blueprint(auth_router)
app.blueprint(listings_router)
app.blueprint(auctioneer_router)
app.blueprint(general_router)

# TEMPLATES CONFIG FOR EMAILS
app.ctx.template_env = env

# EXTRA CONFIGS
app.config.SECRET = settings.SECRET_KEY


@openapi.definition(
    tag="HealthCheck",
    summary="API Health Check",
    description="This endpoint checks the health of the API",
)
@app.route("/ping", methods=["GET", "OPTIONS"], name="Healthcheck")
async def healthcheck(request):
    return json({"success": "pong!"})
