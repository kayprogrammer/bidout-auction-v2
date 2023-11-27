from sanic_testing.testing import SanicASGITestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.managers.accounts import (
    jwt_manager,
    user_manager,
)
from app.db.managers.listings import category_manager, listing_manager
from app.db.managers.base import file_manager
from app.db.models.base import Base

from app.main import app
from app.api.utils.tokens import (
    create_access_token,
    create_refresh_token,
)
from app.common.middlewares import (
    inject_current_user,
    inject_or_remove_session_key,
)
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
import pytest_asyncio, asyncio

test_db = factories.postgresql_proc(port=None, dbname="test_db")

BASE_AUTH_URL_PATH = "/api/v2/auth"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine(test_db):
    pg_host = test_db.host
    pg_port = test_db.port
    pg_user = test_db.user
    pg_db = test_db.dbname
    pg_password = test_db.password

    with DatabaseJanitor(
        pg_user, pg_host, pg_port, pg_db, test_db.version, pg_password
    ):
        connection_str = f"postgresql://{pg_user}:@{pg_host}:{pg_port}/{pg_db}"
        engine = create_engine(connection_str, future=True)
        Base.metadata.create_all(bind=engine)
        yield engine


@pytest_asyncio.fixture(scope="session")
def sort_client(engine):
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestSessionLocal()

    def inject_db_session(request):
        # Inject db to request context
        request.ctx.db = db

    def close_db_session(request, response):
        # close db session
        if hasattr(request.ctx, "db") and request.ctx.db is not None:
            request.ctx.db.close()

    app.register_middleware(inject_db_session, "request")
    app.register_middleware(close_db_session, "response")

    # re-register middlewares that are dependent on our database
    app.register_middleware(inject_current_user, "request")
    app.register_middleware(inject_or_remove_session_key, "response")

    yield {"engine": engine, "database": db, "app": app}


@pytest_asyncio.fixture
async def database(sort_client):
    engine = sort_client["engine"]
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = sort_client["database"]
    yield db
    db.close()


@pytest_asyncio.fixture
async def client(sort_client):
    app = sort_client["app"]
    async with SanicASGITestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def test_user(database):
    create_user_dict = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "testuser123",
    }
    user = user_manager.create(database, create_user_dict)
    database.expunge(user)
    return user


@pytest_asyncio.fixture
async def verified_user(database):
    create_user_dict = {
        "first_name": "TestUser",
        "last_name": "Verified",
        "email": "testverifieduser@example.com",
        "password": "testverifieduser123",
        "is_email_verified": True,
    }

    user = user_manager.create(database, create_user_dict)
    database.expunge(user)
    return user


@pytest_asyncio.fixture
async def another_verified_user(database):
    create_user_dict = {
        "first_name": "AnotherTest",
        "last_name": "UserVerified",
        "email": "anothertestverifieduser@example.com",
        "password": "anothertestverifieduser123",
        "is_email_verified": True,
    }

    user = user_manager.create(database, create_user_dict)
    database.expunge(user)
    return user


@pytest_asyncio.fixture
async def authorized_client(verified_user, client, database):
    access = create_access_token({"user_id": str(verified_user.id)})
    refresh = create_refresh_token()
    jwt_manager.create(
        database,
        {"user_id": verified_user.id, "access": access, "refresh": refresh},
    )
    client.headers = {"Authorization": f"Bearer {access}"}
    return client


@pytest_asyncio.fixture
async def create_listing(verified_user, database):
    # Create Category
    category = category_manager.create(database, {"name": "TestCategory"})

    # Create File
    file = file_manager.create(database, {"resource_type": "image/jpeg"})

    # Create Listing
    listing_dict = {
        "auctioneer_id": verified_user.id,
        "name": "New Listing",
        "desc": "New description",
        "category_id": category.id,
        "price": 1000.00,
        "closing_date": datetime.now() + timedelta(days=1),
        "image_id": file.id,
    }
    listing = listing_manager.create(database, listing_dict)
    database.expunge(listing)
    return {"user": verified_user, "listing": listing, "category": category}
