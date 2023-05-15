from sanic.response import json as sanic_json
from sanic.exceptions import ServerError


def sanic_exceptions_handler(request, exc):
    print(exc)
    if isinstance(exc, ServerError) or not hasattr(exc, "status_code"):
        return sanic_json(
            {
                "status": "failure",
                "message": "Server Error",
            },
            status=500,
        )
    else:
        return sanic_json(
            {
                "status": "failure",
                "message": str(exc),
            },
            status=exc.status_code,
        )


def validation_exception_handler(request, exc):
    # Change default rendering of pydantic validation errors
    errors = exc.errors()
    modified_details = {}
    for error in errors:
        try:
            field_name = error["loc"][1]
        except:
            field_name = error["loc"][0]

        modified_details[f"{field_name}"] = error["msg"]
    return sanic_json(
        {
            "status": "failure",
            "message": "Invalid Entry",
            "data": modified_details,
        },
        status=422,
    )
