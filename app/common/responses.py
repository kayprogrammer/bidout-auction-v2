from sanic.response import json
from datetime import datetime
from uuid import UUID


def convert_to_str(value):
    if isinstance(value, datetime):
        value = str(value.isoformat())
    elif isinstance(value, UUID):
        value = str(value)
    return value


def convert_unserializable_objects_to_string(data):
    if isinstance(data, list):
        for obj in data:
            for key, value in obj.items():
                obj[key] = convert_to_str(value)
    else:
        for key, value in data.items():
            data[key] = convert_to_str(value)
    return data


class CustomResponse:
    @staticmethod
    def success(message, data=None, status_code=200):
        # returns a custom success response

        response = {
            "status": "success",
            "message": message,
            "data": data,
        }

        if data == None:
            response.pop("data")
        else:
            response["data"] = convert_unserializable_objects_to_string(data)

        return json(response, status=status_code)

    @staticmethod
    def error(message, data=None, status_code=400):
        # returns a custom error response

        response = {
            "status": "failure",
            "message": message,
            "data": data,
        }

        response.pop("data") if data == None else response
        return json(response, status=status_code)
