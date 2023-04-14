from app.common.responses import CustomResponse


def validate_quantity(value):
    if value:
        try:
            value = int(value)
        except:
            return CustomResponse.error("Quantity must be an integer")
    return value
