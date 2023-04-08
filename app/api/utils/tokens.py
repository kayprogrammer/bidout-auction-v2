import random
import string
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.db.models.accounts import Jwt, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# generate random string
def get_random(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# generate access token based on user's id
def create_access_token(payload: dict):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, **payload}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# generate random refresh token
def create_refresh_token(
    expire=datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
):
    return jwt.encode(
        {"exp": expire, "data": get_random(10)},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


# verify refresh token
def verify_refresh_token(token):
    try:
        decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except:
        return False


# deocde access token from header
def decodeJWT(db, token):
    if not token:
        return None

    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return None

    if decoded:
        user = db.query(User).filter_by(id=decoded["user_id"]).first()

        if user:
            jwt_obj = db.query(Jwt).filter_by(user_id=user.id).first()
            if not jwt_obj:  # to confirm the validity of the token
                return None
            return user
        return None
