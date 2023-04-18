from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.db.managers.accounts import (
    jwt_manager,
    user_manager,
)
from app.db.managers.listings import category_manager, listing_manager
from contextvars import ContextVar
from app.main import app
from app.api.utils.tokens import (
    create_access_token,
    create_refresh_token,
)
import pytest


TEST_DATABASE = f"{settings.SQLALCHEMY_DATABASE_URL}_test"

engine = create_engine(TEST_DATABASE, future=True)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


BASE_AUTH_URL_PATH = "/api/v2/auth"


@pytest.fixture
def database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(database):
    _base_model_session_ctx = ContextVar("session")

    def inject_db_session(request):
        # Inject db to request context
        request.ctx.db = TestSessionLocal()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.db)

    def close_db_session(request, response):
        # close db session
        if hasattr(request.ctx, "session_ctx_token") and request.ctx.db is not None:
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            request.ctx.db.close()

    app.register_middleware(inject_db_session, "request")
    app.register_middleware(close_db_session, "response")

    yield app.test_client


@pytest.fixture
def test_user(client, database):
    create_user_dict = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "testuser123",
    }
    user = user_manager.create(database, create_user_dict)
    return user


@pytest.fixture
def verified_user(database):
    create_user_dict = {
        "first_name": "TestUser",
        "last_name": "Verified",
        "email": "testverifieduser@example.com",
        "password": "testverifieduser123",
        "is_email_verified": True,
    }

    user = user_manager.create(database, create_user_dict)
    return user


@pytest.fixture
def authorized_client(verified_user, client, database):
    access = create_access_token({"user_id": str(verified_user.id)})
    refresh = create_refresh_token()
    jwt_manager.create(
        database, {"user_id": verified_user.id, "access": access, "refresh": refresh}
    )

    client.headers = {**client.headers, "Bearer": access}
    return client


@pytest.fixture
def create_listing(auctioneer_id, database):
    # Create Category
    category = category_manager.create(database, {"name": "TestCategory"})

    # Create Listing
    listing_dict = {
        "auctioneer_id": auctioneer_id,
        "name": "New Listing",
        "desc": "New description",
        "category_id": category.id,
        "price": 1000.00,
        "closing_date": datetime.now() + timedelta(days=1),
    }
    listing = listing_manager.create(database, listing_dict)

    return {
        "user_id": auctioneer_id,
        "listing_id": listing.id,
    }
