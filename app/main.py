from sanic import Sanic
from sanic.response import json
from sanic_ext import Config
from sanic_ext import openapi
from sanic_session import Session

from textwrap import dedent

from app.core.database import inject_session, close_session
from app.api.routes.auth import auth_router
from app.core.config import settings
from app.common.exception_handlers import (
    sanic_exceptions_handler,
    validation_exception_handler,
)
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader("app", "templates"))


def create_app() -> Sanic:
    app = Sanic(name=settings.PROJECT_NAME)
    app.extend(
        config=Config(
            oas_ui_default="swagger",
            oas_url_prefix="/",
        )
    )
    app.ext.openapi.describe(
        f"{settings.PROJECT_NAME} API",
        version="2",
        description=dedent(
            """
            This is a simple Auction API.
            """
        ),
    )
    app.register_middleware(inject_session, "request")
    app.register_middleware(close_session, "response")
    app.register_middleware(validation_exception_handler, "response")

    app.error_handler.add(Exception, sanic_exceptions_handler)

    app.blueprint(auth_router)
    app.ctx.template_env = env
    Session(app)
    return app


app = create_app()


@openapi.definition(
    tag="HealthCheck",
    summary="API Health Check",
    description="This endpoint checks the health of the API",
)
@app.get("/ping", name="Healthcheck")
async def healthcheck(request):
    return json({"success": "pong!"})
