from functools import wraps
from sanic import Request
from sanic.exceptions import SanicException


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
