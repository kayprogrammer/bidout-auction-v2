from http import HTTPStatus
from typing import Optional
from sanic.response import json
from sanic.exceptions import ServerError
from pydantic import ValidationError


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class RequestError(Error):
    def __init__(
        self, status_code: int, status_msg: str, error_msg: Optional[str] = None
    ):
        self.status_code = HTTPStatus(status_code)
        self.status_msg = status_msg
        self.error_msg = error_msg


class RequestErrorHandler:
    def __init__(self, exc: RequestError):
        self.status_msg = exc.status_msg
        self.status_code = exc.status_code
        self.error_msg = exc.error_msg

    def process_message(self):
        return json(
            {
                "status": self.status_msg,
                "message": self.error_msg,
            },
            status=self.status_code,
        )


def sanic_exceptions_handler(request, exc):
    if not isinstance(exc, ServerError):
        return json(
            {
                "status": "failure",
                "message": "Server Error",
            },
            status=exc.status_code,
        )
    elif not isinstance(exc, ValidationError):
        return json(
            {
                "status": "failure",
                "message": str(exc),
            },
            status=exc.status_code,
        )


def validation_exception_handler(request, exc: ValidationError):
    print(exc)
    # Get the original 'detail' list of errors
    details = exc.errors()
    modified_details = {}
    for error in details:
        try:
            field_name = error["loc"][1]
        except:
            field_name = error["loc"][0]

        modified_details[f"{field_name}"] = error["msg"]
    return json(
        {
            "status": "failure",
            "message": "Invalid Entry",
            "data": modified_details,
        },
        status_code=422,
    )
