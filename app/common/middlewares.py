from app.api.utils.tokens import decodeJWT
from app.db.managers.base import user_session_manager
from app.db.models.accounts import User
from app.core.config import settings


def add_cors_headers(request, response):
    origin = request.headers.get("origin")
    allowed_origins = settings.CORS_ALLOWED_ORIGINS
    allowed_origin = origin if origin in allowed_origins else allowed_origins[0]

    headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "origin, content-type, accept, authorization, x-xsrf-token, x-request-id",
    }
    response.headers.extend(headers)


class RequestUserObject(object):
    def __init__(self, user, is_authenticated=False):
        # initialize values
        self.user = user
        self.is_authenticated = is_authenticated

    def __str__(self):
        # Return name if it's a user object, otherwise return the session_key
        user = self.user
        if isinstance(user, User):
            user = user.full_name()
        return user

    def __getattr__(self, attr):
        # Ensure that is_authenticated attribute returns directly from the object even if
        # its not a column of the user model object (Just like Django).
        if attr == "is_authenticated":
            return self.is_authenticated
        else:
            return getattr(self.user, attr)


def inject_current_user(request):
    # Inject current user to the request context.
    db = request.ctx.db
    token = request.headers.get("Authorization", None)  # can also use request.token
    is_authorized = decodeJWT(db, token)
    if is_authorized:
        # Let the user context object contain the user model object
        request.ctx.user = RequestUserObject(user=is_authorized, is_authenticated=True)
    else:
        # Let the user context object contain a session key
        session_key = request.cookies.get("session_key")
        if not session_key:
            session_key_obj = user_session_manager.create(db)
            session_key = str(session_key_obj.id)
        request.ctx.user = RequestUserObject(user=session_key)


def inject_or_remove_session_key(request, response):
    # Add or remove session key to cookies based on authorization status.
    # This cannot be done in the inject_current_user because cookies are added via responses.

    db = request.ctx.db
    if request.ctx.user.is_authenticated:
        session_key = request.cookies.get("session_key")
        if session_key:
            user_session_manager.delete_by_id(db, session_key)
            response.delete_cookie("session_key")
    else:
        session_key = request.cookies.get("session_key")
        if not session_key:
            response.add_cookie(
                "session_key",
                str(request.ctx.user),
                max_age=1209600,
                httponly=True,
                samesite="none",
            )
