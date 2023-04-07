from http import HTTPStatus
from typing import Optional
from sanic.response import json as sanic_json
from sanic.exceptions import ServerError, BadRequest, NotFound
from pydantic import ValidationError
import json


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
        return sanic_json(
            {
                "status": self.status_msg,
                "message": self.error_msg,
            },
            status=self.status_code,
        )


def sanic_exceptions_handler(request, exc):
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
    if exc.status == 422:
        errors = json.loads(exc.body)

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
