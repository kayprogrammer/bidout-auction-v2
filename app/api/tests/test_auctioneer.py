from app.db.managers.accounts import jwt_manager
from app.db.managers.listings import category_manager, bid_manager
from app.api.utils.tokens import create_access_token, create_refresh_token
from datetime import datetime, timedelta
from pytz import UTC
import mock

BASE_URL_PATH = "/api/v2/auctioneer"


async def test_profile_view(authorized_client, verified_user):
    _, response = await authorized_client.get(f"{BASE_URL_PATH}/")
    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "User details fetched!",
        "data": {
            "first_name": verified_user.first_name,
            "last_name": verified_user.last_name,
            "avatar": mock.ANY,
        },
    }


async def test_profile_update(authorized_client):
    user_dict = {
        "first_name": "VerifiedUser",
        "last_name": "Update",
        "file_type": "image/jpeg",
    }
    _, response = await authorized_client.put(f"{BASE_URL_PATH}/", json=user_dict)
    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "User updated!",
        "data": {
            "first_name": "VerifiedUser",
            "last_name": "Update",
            "file_upload_data": mock.ANY,
        },
    }


async def test_auctioneer_retrieve_listings(authorized_client, create_listing):
    # Verify that all listings by a particular auctioneer is fetched
    _, response = await authorized_client.get(f"{BASE_URL_PATH}/listings")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Auctioneer Listings fetched"
    data = json_resp["data"]
    assert len(data) > 0
    assert any(isinstance(obj["name"], str) for obj in data)


async def test_auctioneer_create_listings(authorized_client, database):
    # Create Category
    await category_manager.create(database, {"name": "Test Category"})

    listing_dict = {
        "name": "Test Listing",
        "desc": "Test description",
        "category": "test-category",
        "price": 1000.00,
        "closing_date": str(
            (datetime.utcnow() + timedelta(days=1)).replace(tzinfo=UTC)
        ),
        "file_type": "image/jpeg",
    }

    # Verify that create listing succeeds with a valid category
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/listings", json=listing_dict
    )
    assert response.status_code == 201
    assert response.json == {
        "status": "success",
        "message": "Listing created successfully",
        "data": {
            "name": "Test Listing",
            "auctioneer": mock.ANY,  # cos our pydantic validator uses SessionLocal and not TestSessionLocal
            "slug": "test-listing",
            "desc": "Test description",
            "category": mock.ANY,  # cos our pydantic validator uses SessionLocal and not TestSessionLocal
            "price": 1000,
            "closing_date": mock.ANY,
            "active": True,
            "bids_count": 0,
            "file_upload_data": mock.ANY,
        },
    }

    # Verify that create listing failed with invalid category
    listing_dict.update({"category": "invalidcategory"})
    _, response = await authorized_client.post(
        f"{BASE_URL_PATH}/listings", json=listing_dict
    )
    assert response.status_code == 422
    assert response.json == {
        "status": "failure",
        "message": "Invalid entry",
        "data": {"category": "Invalid category"},
    }


async def test_auctioneer_update_listing(authorized_client, create_listing):
    listing = create_listing["listing"]

    listing_dict = {
        "name": "Test Listing Updated",
        "desc": "Test description Updated",
        "category": "invalidcategory",
        "price": 2000.00,
        "closing_date": str(
            (datetime.utcnow() + timedelta(days=1)).replace(tzinfo=UTC)
        ),
        "file_type": "image/png",
    }

    # Verify that update listing failed with invalid listing slug
    _, response = await authorized_client.patch(
        f"{BASE_URL_PATH}/listings/invalid_slug", json=listing_dict
    )
    assert response.status_code == 404
    assert response.json == {
        "status": "failure",
        "message": "Listing does not exist!",
    }

    # Verify that update listing failed with invalid category
    _, response = await authorized_client.patch(
        f"{BASE_URL_PATH}/listings/{listing.slug}", json=listing_dict
    )
    assert response.status_code == 422
    assert response.json == {
        "status": "failure",
        "message": "Invalid entry",
        "data": {"category": "Invalid category"},
    }

    # Verify that update listing succeeds with a valid category
    listing_dict.update({"category": "testcategory"})
    _, response = await authorized_client.patch(
        f"{BASE_URL_PATH}/listings/{listing.slug}", json=listing_dict
    )
    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "Listing updated successfully",
        "data": {
            "name": "Test Listing Updated",
            "auctioneer": mock.ANY,  # cos our pydantic validator uses SessionLocal and not TestSessionLocal
            "slug": "test-listing-updated",
            "desc": "Test description Updated",
            "category": mock.ANY,  # cos our pydantic validator uses SessionLocal and not TestSessionLocal
            "price": 2000,
            "closing_date": mock.ANY,
            "active": True,
            "bids_count": 0,
            "file_upload_data": mock.ANY,
        },
    }

    # You can also test for invalid users yourself.....


async def test_auctioneer_listings_bids(
    authorized_client, create_listing, another_verified_user, database
):
    listing = create_listing["listing"]

    # Create Bid
    await bid_manager.create(
        database,
        {
            "user_id": another_verified_user.id,
            "listing_id": listing.id,
            "amount": 5000.00,
        },
    )

    # Verify that auctioneer listing bids retrieval succeeds with a valid slug and owner
    _, response = await authorized_client.get(
        f"{BASE_URL_PATH}/listings/{listing.slug}/bids"
    )
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Listing Bids fetched"
    data = json_resp["data"]
    assert isinstance(data["listing"], str)

    # Verify that the auctioneer listing bids retrieval failed with invalid listing slug
    _, response = await authorized_client.get(
        f"{BASE_URL_PATH}/listings/invalid_slug/bids"
    )
    assert response.status_code == 404
    assert response.json == {"status": "failure", "message": "Listing does not exist!"}

    # Verify that the auctioneer listing bids retrieval failed with invalid owner
    access = create_access_token({"user_id": str(another_verified_user.id)})
    refresh = create_refresh_token()
    await jwt_manager.create(
        database,
        {"user_id": another_verified_user.id, "access": access, "refresh": refresh},
    )

    _, response = await authorized_client.get(
        f"{BASE_URL_PATH}/listings/{listing.slug}/bids",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 400
    assert response.json == {
        "status": "failure",
        "message": "This listing doesn't belong to you!",
    }
