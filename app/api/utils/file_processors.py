from sanic import Sanic
from app.core.config import settings
from app.common.responses import CustomResponse
import mimetypes
import time

app = Sanic.get_app()
cloudinary = app.ctx.cloudinary
BASE_FOLDER = "bidout-auction-v2/"


class FileProcessor:
    @staticmethod
    def generate_file_url(key, folder, content_type):
        file_extension = mimetypes.guess_extension(content_type)
        key = f"{BASE_FOLDER}{folder}{key}{file_extension}"
        params = {
            "public_id": key,
            "timestamp": str(int(time.time())),
        }
        try:
            signed_url, options = cloudinary.utils.cloudinary_url(
                key,
                transformation={"width": 500, "height": 500, "crop": "fill"},
                resource_type="image",
                type="authenticated",
                **params,
            )
            return signed_url
        except Exception as e:
            print(e)
            return CustomResponse.error("Couldn't generate file url!")
