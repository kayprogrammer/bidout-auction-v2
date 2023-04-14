from app.common.responses import CustomResponse
from app.core.config import settings
import mimetypes
import time
import cloudinary

BASE_FOLDER = "bidout-auction-v2/"

# FILES CONFIG WITH CLOUDINARY
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


class FileProcessor:
    @staticmethod
    def generate_file_url(key, folder, content_type):
        file_extension = mimetypes.guess_extension(content_type)
        key = f"{BASE_FOLDER}{folder}/{key}{file_extension}"
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


# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODE3Mjg0MjksInVzZXJfaWQiOiJkMmVhNjU2Ni05YTM0LTQxNWYtOTA3NS0wMTVjMTU0MjUwOTgifQ.I7IZ3VStZGjZ6q5ajfNDtUhFysnWeAcd3AMuK3FoUaU
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODE3Mjg0NzYsInVzZXJfaWQiOiIxNDhmMTlkNC0zYWQ0LTRlNjMtYWNjNS0zZTkxOWJlOWQ1N2EifQ.30JsBIDsAGIAHpJRXpaLSlB4hUoRBMse9czy-66_4sE
