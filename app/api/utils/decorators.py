from functools import wraps
from app.common.responses import CustomResponse
from .tokens import decodeJWT


def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            db = request.ctx.db
            token = request.headers.get("Authorization", None)
            is_authorized = decodeJWT(db, token)

            if is_authorized:
                # Add the user to the request context
                request.ctx.user = is_authorized
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return CustomResponse.error("Unauthorized User", status_code=401)

        return decorated_function

    return decorator
