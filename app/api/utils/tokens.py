import random
import string
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.db.managers.accounts import user_manager, jwt_manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# generate random string
def get_random(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


# generate access token based and encode user's id
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
        jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except:
        return False


# deocde access token from header
async def decodeJWT(db, token):
    if not token:
        return None

    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return None

    if decoded:
        jwt_obj = await jwt_manager.get_by_user_id(db, decoded["user_id"])
        if not jwt_obj:
            return None
        return jwt_obj.user
