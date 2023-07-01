from app.db.managers.accounts import jwt_manager
from app.db.managers.listings import category_manager, watchlist_manager, bid_manager
from app.api.utils.tokens import create_access_token, create_refresh_token
import pytest
import mock

BASE_URL_PATH = "/api/v2/listings"


@pytest.mark.asyncio
async def test_retrieve_all_listings(client, create_listing):
    # Verify that all listings are retrieved successfully
    _, response = await client.get(f"{BASE_URL_PATH}")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Listings fetched"
    data = json_resp["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


@pytest.mark.asyncio
async def test_retrieve_particular_listng(client, create_listing):
    listing = create_listing["listing"]

    # Verify that a particular listing retrieval fails with an invalid slug
    _, response = await client.get(f"{BASE_URL_PATH}/detail/invalid_slug")
    assert response.status_code == 404
    assert response.json == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that a particular listing is retrieved successfully
    _, response = await client.get(f"{BASE_URL_PATH}/detail/{listing.slug}")
    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "Listing details fetched",
        "data": {
            "listing": {
                "name": listing.name,
                "auctioneer": mock.ANY,  # cos our pydantic validator uses SessionLocal and not TestSessionLocal
                "slug": listing.slug,
                "desc": listing.desc,
                "category": mock.ANY,  # cos our pydantic validator uses SessionLocal and not TestSessionLocal
                "price": listing.price,
                "closing_date": mock.ANY,
                "time_left_seconds": mock.ANY,
                "active": True,
                "bids_count": 0,
                "highest_bid": 0,
                "image": mock.ANY,
                "watchlist": None,
            },
            "related_listings": [],
        },
    }


@pytest.mark.asyncio
async def test_get_user_watchlists_listng(authorized_client, create_listing, database):
    listing = create_listing["listing"]
    user_id = create_listing["user"].id
    watchlist_manager.create(database, {"user_id": user_id, "listing_id": listing.id})

    _, response = await authorized_client.get(f"{BASE_URL_PATH}/watchlist")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Watchlists Listings fetched"
    data = json_resp["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


@pytest.mark.asyncio
async def test_create_or_remove_user_watchlists_listng(
    authorized_client, create_listing
):
    listing = create_listing["listing"]

    # Verify that the endpoint fails with an invalid slug
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/watchlist", json={"slug": "invalid_slug"}
    )
    assert response.status_code == 404
    assert response.json == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that the watchlist was created successfully
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/watchlist", json={"slug": listing.slug}
    )
    assert response.status_code == 201
    assert response.json == {
        "status": "success",
        "message": "Listing added to user watchlist",
    }


@pytest.mark.asyncio
async def test_retrieve_all_categories(client, database):
    # Create Category
    category_manager.create(database, {"name": "TestCategory"})

    # Verify that all categories are retrieved successfully
    _, response = await client.get(f"{BASE_URL_PATH}/categories")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Categories fetched"
    data = json_resp["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


@pytest.mark.asyncio
async def test_retrieve_all_listings_by_category(client, create_listing):
    slug = create_listing["category"].slug

    # Verify that listings by an invalid category slug fails
    _, response = await client.get(f"{BASE_URL_PATH}/categories/invalid_category_slug")
    assert response.status_code == 404
    assert response.json == {"status": "failure", "message": "Invalid category"}

    # Verify that all listings by a valid category slug are retrieved successfully
    _, response = await client.get(f"{BASE_URL_PATH}/categories/{slug}")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Category Listings fetched"
    data = json_resp["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


@pytest.mark.asyncio
async def test_retrieve_listing_bids(
    client, create_listing, another_verified_user, database
):
    listing = create_listing["listing"]

    bid_manager.create(
        database,
        {
            "user_id": another_verified_user.id,
            "listing_id": listing.id,
            "amount": 10000,
        },
    )

    # Verify that listings by an invalid listing slug fails
    _, response = await client.get(f"{BASE_URL_PATH}/detail/invalid_category_slug/bids")
    assert response.status_code == 404
    assert response.json == {"status": "failure", "message": "Listing does not exist!"}

    # Verify that all listings by a valid listing slug are retrieved successfully
    _, response = await client.get(f"{BASE_URL_PATH}/detail/{listing.slug}/bids")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Listing Bids fetched"
    data = json_resp["data"]
    assert isinstance(data["listing"], str)


@pytest.mark.asyncio
async def test_create_bid(
    authorized_client, create_listing, another_verified_user, database
):
    listing = create_listing["listing"]

    # Verify that the endpoint fails with an invalid slug
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/invalid_listing_slug/bids", json={"amount": 10000}
    )
    assert response.status_code == 404
    assert response.json == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that the endpoint fails with an invalid user
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/{listing.slug}/bids", json={"amount": 10000}
    )
    assert response.status_code == 403
    assert response.json == {
        "status": "failure",
        "message": "You cannot bid your own product!",
    }

    # Update headers with another user's token
    access = create_access_token({"user_id": str(another_verified_user.id)})
    refresh = create_refresh_token()
    jwt_manager.create(
        database,
        {"user_id": another_verified_user.id, "access": access, "refresh": refresh},
    )
    authorized_client.headers = {"Authorization": f"Bearer {access}"}

    # Verify that the endpoint fails with a lesser bidding price
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/{listing.slug}/bids", json={"amount": 100}
    )
    assert response.status_code == 400
    assert response.json == {
        "status": "failure",
        "message": "Bid amount cannot be less than the bidding price!",
    }

    # Verify that the bid was created successfully
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/detail/{listing.slug}/bids", json={"amount": 10000}
    )
    assert response.status_code == 201
    assert response.json == {
        "status": "success",
        "message": "Bid added to listing",
        "data": {
            "id": mock.ANY,
            "user": mock.ANY,
            "amount": 10000,
            "created_at": mock.ANY,
            "updated_at": mock.ANY,
        },
    }

    # You can also test for other error responses.....
