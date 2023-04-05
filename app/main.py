from sanic import Sanic
from sanic.response import json
from sanic_ext import Config
from textwrap import dedent
from sanic_ext import openapi

from app.api.routes.auth import bp
from app.core.config import settings


def create_app() -> Sanic:
    app = Sanic(name=settings.PROJECT_NAME)
    app.extend(config=Config(oas_ui_default="swagger", oas_url_prefix="/"))
    app.ext.openapi.describe(
        f"{settings.PROJECT_NAME} API",
        version="2",
        description=dedent(
            """
            This is a simple Auction API.
            """
        ),
    )
    app.blueprint(bp)
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
