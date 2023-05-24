from app.common.responses import CustomResponse
from app.core.config import settings
import time
import cloudinary
import mimetypes

BASE_FOLDER = "bidout-auction-v2/"

# FILES CONFIG WITH CLOUDINARY
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


class FileProcessor:
    @staticmethod
    def generate_file_signature(key, folder):
        key = f"{BASE_FOLDER}{folder}/{key}"
        timestamp = str(int(time.time()))
        params = {
            "public_id": key,
            "timestamp": timestamp,
        }
        try:
            signature = cloudinary.utils.api_sign_request(
                params_to_sign = params,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
            return {"public_id": key, "signature": signature, "timestamp": timestamp}
        except Exception as e:
            print(e)
            return CustomResponse.error("Couldn't generate signature")
        
    def generate_file_url(key, folder, content_type):
        file_extension = mimetypes.guess_extension(content_type)
        key = f"{BASE_FOLDER}{folder}/{key}{file_extension}"
        
        try:
            return cloudinary.utils.cloudinary_url(key, secure=True)
        except Exception as e:
            print(e)
            return CustomResponse.error("Couldn't generate file url!")

