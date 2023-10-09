from app.api.utils.tokens import decodeJWT
from app.db.managers.base import guest_user_manager
from app.core.config import settings


def add_cors_headers(request, response):
    origin = request.headers.get("origin")
    allowed_origins = settings.CORS_ALLOWED_ORIGINS
    allowed_origin = origin if origin in allowed_origins else allowed_origins[0]

    headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "origin, content-type, accept, authorization, x-xsrf-token, x-request-id, guestuserid",
    }
    response.headers.extend(headers)


def inject_current_user(request):
    # Inject current user to the request context.
    db = request.ctx.db
    token = request.headers.get("Authorization", None)  # can also use request.token
    is_authorized = decodeJWT(db, token)
    if is_authorized:
        # Let the user context object contain the user model object
        request.ctx.user = is_authorized
    else:
        # Let the user context object contain a guest user model object
        guestuser_id = request.headers.get("guestuserid", None)
        guestuser = guest_user_manager.get_or_create(db, guestuser_id)
        request.ctx.user = guestuser
