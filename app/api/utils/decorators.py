from functools import wraps
from app.common.responses import CustomResponse
from .tokens import decodeJWT


def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            if request.ctx.user.is_authenticated:
                response = await f(request, *args, **kwargs)
                return response
            else:
                return CustomResponse.error("Unauthorized User", status_code=401)

        return decorated_function

    return decorator
