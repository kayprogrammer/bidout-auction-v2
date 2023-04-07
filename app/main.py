from sanic import Sanic
from sanic.response import json
from sanic.exceptions import (
    BadRequest,
    RequestCancelled,
    RequestTimeout,
    HTTPException,
)
from sanic_ext import Config
from sanic_ext import openapi
from sanic_jinja2 import SanicJinja2
from sanic_mail import Sanic_Mail

from textwrap import dedent

from app.core.database import inject_session, close_session
from app.api.routes.auth import auth_router
from app.core.config import settings
from app.common.exception_handlers import (
    sanic_exceptions_handler,
    validation_exception_handler,
)


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
    app.config.update(settings.MAIL_CONFIG)
    return app


app = create_app()
jinja = SanicJinja2(app)
sender = Sanic_Mail(app)


@openapi.definition(
    tag="HealthCheck",
    summary="API Health Check",
    description="This endpoint checks the health of the API",
)
@app.get("/ping", name="Healthcheck")
async def healthcheck(request):
    return json({"success": "pong!"})
