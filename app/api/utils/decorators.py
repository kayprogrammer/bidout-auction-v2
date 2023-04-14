from functools import wraps
from app.common.responses import CustomResponse
from sanic import json, Request
from pydantic import ValidationError


def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if not isinstance(request, Request):
                request = args[0]
            # run some method that checks the request
            # for the client's authorization status
            if request.ctx.user.is_authenticated:
                response = await f(request, *args, **kwargs)
                return response
            else:
                return CustomResponse.error("Unauthorized User", status_code=401)

        return decorated_function

    return decorator


def validate_request(schema):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if not isinstance(request, Request):  # Important for CBVs
                request = args[0]
            try:
                data = schema(**request.json)
                kwargs.update(data.dict())
            except ValidationError as e:
                print(e)
                return json({"error": e.errors()}, status=422)
            return await f(request, *args, **kwargs)

        return decorated_function

    return decorator
