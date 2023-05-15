from functools import wraps
from app.common.responses import CustomResponse
from sanic import Request
from sanic.exceptions import SanicException


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
            data = schema(**request.json)
            data_dict = data.dict()
            request.json.update(data_dict)
            kwargs.update(data_dict)
            return await f(request, *args, **kwargs)

        return decorated_function

    return decorator
