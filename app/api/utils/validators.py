from sanic import SanicException


def validate_quantity(value):
    if value:
        try:
            value = int(value)
        except:
            raise SanicException(message="Quantity must be an integer", status_code=400)
    return value
