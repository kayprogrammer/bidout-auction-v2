from app.db.managers.general import review_manager
import pytest
import mock

BASE_URL_PATH = "/api/v2/general"


@pytest.mark.asyncio
async def test_retrieve_sitedetail(client):
    # Check response validity
    _, response = await client.get(f"{BASE_URL_PATH}/site-detail")
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp["status"] == "success"
    assert json_resp["message"] == "Site Details fetched"
    keys = ["name", "email", "phone", "address", "fb", "tw", "wh", "ig"]
    assert all(item in json_resp["data"] for item in keys)


@pytest.mark.asyncio
async def test_suscribe(client):
    suscriber_dict = {"email": "test_suscriber@example.com"}

    # Check response validity
    _, response = await client.post(f"{BASE_URL_PATH}/suscribe", json=suscriber_dict)
    assert response.status_code == 201
    assert response.json == {
        "status": "success",
        "message": "Suscriber added successfully",
        "data": {"email": "test_suscriber@example.com"},
    }


@pytest.mark.asyncio
async def test_retrieve_reviews(client, verified_user, database):
    # Create test reviews
    review_dict = {
        "reviewer_id": verified_user.id,
        "show": True,
        "text": "This is a nice platform",
    }
    review_manager.create(database, review_dict)

    # Check response validity
    _, response = await client.get(f"{BASE_URL_PATH}/reviews")
    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "Reviews fetched",
        "data": [{"reviewer": mock.ANY, "text": "This is a nice platform"}],
    }
