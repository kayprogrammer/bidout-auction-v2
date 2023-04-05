from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextvars import ContextVar
from .config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

_base_model_session_ctx = ContextVar("session")

Base = declarative_base()


async def inject_session(request):
    request.ctx.session = SessionLocal()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(
        request.ctx.session
    )


async def close_session(request, response):
    if (
        hasattr(request.ctx, "session_ctx_token")
        and request.ctx.session is not None
    ):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        request.ctx.session.close()
