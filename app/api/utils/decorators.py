from functools import wraps
from app.common.responses import CustomResponse
from sanic import Request
from sanic.exceptions import SanicException
import re


def check_endpoint(value):
    endpoints = [
        "/api/v2/listings/?$",
        "/api/v2/listings/watchlist/?$",
        "/api/v2/listings/categories/[\w-]+/?$",
    ]
    # Make a regex that matches if any of our regexes match.
    combined = "(" + ")|(".join(endpoints) + ")"

    if re.match(combined, value):
        return True
    return False


def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if not isinstance(request, Request):
                request = args[0]
            # run some method that checks the request
            # for the client's authorization status
            access_token = request.token
            if request.ctx.user.is_authenticated or (
                check_endpoint(request.path) and not access_token
            ):
                response = await f(request, *args, **kwargs)
                return response

            else:
                return CustomResponse.error("Unauthorized user", status_code=401)

        return decorated_function

    return decorator


def validate_request(schema):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if not isinstance(request, Request):  # Important for CBVs
                request = args[0]
            json_data = request.json
            if not json_data:
                raise SanicException(
                    message="Invalid request. Missing body", status_code=400
                )
            data = schema(**json_data)
            data_dict = data.dict()
            kwargs.update({"data": data_dict})
            return await f(request, *args, **kwargs)

        return decorated_function

    return decorator
