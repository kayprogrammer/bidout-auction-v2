from sanic.response import json


class CustomResponse:
    @staticmethod
    def success(message, data=None, status_code=200):
        response = {
            "status": "success",
            "message": message,
            "data": data,
        }

        response.pop("data") if data == None else response
        return json(response, status=status_code)

    @staticmethod
    def error(message, data=None, status_code=400):
        response = {
            "status": "failure",
            "message": message,
            "data": data,
        }

        response.pop("data") if data == None else response
        return json(response, status=status_code)
