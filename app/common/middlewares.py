from typing import Iterable
from app.api.utils.tokens import decodeJWT
from app.db.managers.base import user_session_manager
from app.db.models.accounts import User


def _add_cors_headers(response, methods: Iterable[str]) -> None:
    allow_methods = list(set(methods))
    if "OPTIONS" not in allow_methods:
        allow_methods.append("OPTIONS")
    headers = {
        "Access-Control-Allow-Methods": ",".join(allow_methods),
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": (
            "origin, content-type, accept, " "authorization, x-xsrf-token, x-request-id"
        ),
    }
    response.headers.extend(headers)


def add_cors_headers(request, response):
    if request.method != "OPTIONS":
        methods = [method for method in request.route.methods]
        _add_cors_headers(response, methods)


class RequestUserObject(object):
    def __init__(self, user, is_authenticated=False):
        self.user = user
        self.is_authenticated = is_authenticated

    def __str__(self):
        user = self.user
        if isinstance(user, User):
            user = user.full_name()
        return user

    def __getattr__(self, attr):
        if attr == "is_authenticated":
            return self.is_authenticated
        else:
            return getattr(self.user, attr)


def inject_current_user(request):
    db = request.ctx.db
    token = request.headers.get("Authorization", None)
    is_authorized = decodeJWT(db, token)
    if is_authorized:
        request.ctx.user = RequestUserObject(user=is_authorized, is_authenticated=True)
    else:
        session_key = request.cookies.get("session_key")
        if not session_key:
            session_key_obj = user_session_manager.create(db)
            session_key = str(session_key_obj.id)
        request.ctx.user = RequestUserObject(user=session_key)


def inject_or_remove_session_key(request, response):
    db = request.ctx.db
    if request.ctx.user.is_authenticated:
        session_key = request.cookies.get("session_key")
        if session_key:
            user_session_manager.delete_by_id(db, session_key)
            response.delete_cookie("session_key")
    else:
        session_key = request.cookies.get("session_key")
        if not session_key:
            response.add_cookie("session_key", str(request.ctx.user), max_age=1209600)
