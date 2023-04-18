from sanic import Sanic
from sanic.response import json
from sanic_ext import Config, openapi

from app.core.database import inject_db_session, close_db_session
from app.api.routes.auth import auth_router
from app.api.routes.listings import listings_router
from app.api.routes.auctioneer import auctioneer_router


from app.core.config import settings
from app.common.exception_handlers import (
    sanic_exceptions_handler,
    validation_exception_handler,
)
from app.common.middlewares import (
    add_cors_headers,
    inject_current_user,
    inject_or_remove_session_key,
)

from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader("app", "templates"))


def create_app() -> Sanic:
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
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    app.ext.openapi.secured("token")
    # --------------------------

    # REGISTER MIDDLEWARES
    app.register_middleware(inject_db_session, "request")
    app.register_middleware(close_db_session, "response")
    app.register_middleware(inject_current_user, "request")
    app.register_middleware(inject_or_remove_session_key, "response")
    app.register_middleware(validation_exception_handler, "response")
    app.register_middleware(add_cors_headers, "response")

    # EXCEPTION HANDLERS
    app.error_handler.add(Exception, sanic_exceptions_handler)

    # REGISTER BLUEPRINTS
    app.blueprint(auth_router)
    app.blueprint(listings_router)
    app.blueprint(auctioneer_router)

    # TEMPLATES CONFIG FOR EMAILS
    app.ctx.template_env = env

    # EXTRA CONFIGS
    app.config.SECRET = settings.SECRET_KEY
    app.config.CORS_ORIGINS = settings.CORS_ALLOWED_ORIGINS
    return app


app = create_app()
test_client = app.test_client


@openapi.definition(
    tag="HealthCheck",
    summary="API Health Check",
    description="This endpoint checks the health of the API",
)
@app.get("/ping", name="Healthcheck")
async def healthcheck(request):
    return json({"success": "pong!"})
