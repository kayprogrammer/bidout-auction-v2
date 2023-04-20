from app.db.managers.listings import listing_manager, category_manager

from datetime import datetime, timedelta
import pytest
import mock

BASE_URL_PATH = "/api/v2/auctioneer"


@pytest.mark.asyncio
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


# @pytest.mark.asyncio
# async def test_auctioneer_create_listings(authorized_client, verified_user, database):
#     # Create Category
#     category_manager.create(database, {"name": "Test Category"})

#     listing_dict = {
#         "name": "Test Listing",
#         "desc": "Test description",
#         "category": "test-category",
#         "price": 1000.00,
#         "closing_date": datetime.now() + timedelta(days=1),
#         "file_type": "image/jpeg",
#     }

#     # Verify that create listing succeeds with a valid category
#     _, response = await authorized_client.post(f"{BASE_URL_PATH}/listings", json=listing_dict)
#     assert response.status_code == 201
#     assert response.json == {
#         "status": "success",
#         "message": "Listing created successfully",
#         "data": {
#             "name": "Test Listing",
#             "auctioneer": {
#                 "name": verified_user.name,
#                 "avatar": mock.ANY
#             },
#             "slug": "test-listing",
#             "desc": "Test description",
#             "category": "Test Category",
#             "price": 1000.00,
#             "closing_date": mock.ANY,
#             "active": True,
#             "bids_count": 0,
#             "upload_url": mock.ANY,
#         }
#     }

#     # Verify that create listing failed with invalid category
#     listing_dict.update({"category": "invalidcategory"})
#     _, response = await authorized_client.post(f"{BASE_URL_PATH}/listings", json=listing_dict)
#     assert response.status_code == 422
#     assert response.json == {
#         "status": "failure",
#         "message": "Invalid entry",
#         "data": {
#             "category": "Invalid category"
#         }
#     }
