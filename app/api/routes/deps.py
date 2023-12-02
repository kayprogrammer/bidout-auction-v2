from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession
from sanic import Request, SanicException

from app.api.utils.tokens import decodeJWT
from app.db.managers.base import guestuser_manager
from app.db.models.accounts import User
from app.db.models.base import GuestUser


class Client:
    pass


class AuthUser:
    pass


async def get_client(request: Request, db: AsyncSession) -> Union[User, GuestUser]:
    token = request.headers.get("Authorization", None)  # can also use request.token
    if token:
        is_authorized = await decodeJWT(db, token[7:])
        if not is_authorized:
            raise SanicException(
                message="Auth Token is invalid or expired", status_code=401
            )
        return is_authorized
    guestuser_id = request.headers.get("guestuserid", None)
    guestuser = await guestuser_manager.get_or_create(db, guestuser_id)
    return guestuser


async def get_user(request: Request, db: AsyncSession) -> User:
    token = request.token
    if not token:
        raise SanicException(message="Unauthorized user", status_code=401)
    user = await decodeJWT(db, token)
    if not user:
        raise SanicException(
            message="Auth Token is invalid or expired", status_code=401
        )
    return user
