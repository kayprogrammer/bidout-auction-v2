from app.core.config import settings


def add_cors_headers(request, response):
    origin = request.headers.get("origin")
    allowed_origins = settings.CORS_ALLOWED_ORIGINS
    allowed_origin = origin if origin in allowed_origins else allowed_origins[0]

    headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "origin, content-type, accept, authorization, x-xsrf-token, x-request-id, guestuserid",
    }
    response.headers.extend(headers)
