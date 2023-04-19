from app.db.managers.accounts import user_manager, jwt_manager, otp_manager
from app.api.utils.tokens import create_refresh_token
import pytest
import mock

BASE_URL_PATH = "/api/v2/auth"


@pytest.mark.asyncio
async def test_register_user(client):
    # Setup
    email = "testregisteruser@example.com"
    password = "testregisteruserpassword"
    user_in = {
        "first_name": "Testregister",
        "last_name": "User",
        "email": email,
        "password": password,
    }

    # Verify that a new user can be registered successfully
    with mock.patch("app.api.utils.emails.send_email") as send_verification_email_mock:
        _, response = await client.post(f"{BASE_URL_PATH}/register", json=user_in)
        assert response.status_code == 201
        assert response.json == {
            "status": "success",
            "message": "Registration successful",
        }

    # Verify that a user with the same email cannot be registered again
    with mock.patch("app.api.utils.emails.send_email") as send_verification_email_mock:
        _, response = await client.post(f"{BASE_URL_PATH}/register", json=user_in)
        assert response.status_code == 422
        assert response.json == {
            "status": "failure",
            "message": "Invalid Entry",
            "data": {"email": "Email already registered!"},
        }


@pytest.mark.asyncio
async def test_verify_email(client, test_user, database):
    user = test_user
    otp = "111111"

    # Verify that the email verification fails with an invalid otp
    _, response = await client.post(
        f"{BASE_URL_PATH}/verify-email", json={"email": user.email, "otp": otp}
    )
    assert response.status_code == 400
    assert response.json == {
        "status": "failure",
        "message": "Incorrect Otp",
    }

    # Verify that the email verification succeeds with a valid otp
    otp = otp_manager.create(database, {"user_id": user.id})
    with mock.patch("app.api.utils.emails.send_email") as send_welcome_email_mock:
        _, response = await client.post(
            f"{BASE_URL_PATH}/verify-email",
            json={"email": user.email, "otp": otp.code},
        )
        assert response.status_code == 200
        assert response.json == {
            "status": "success",
            "message": "Account verification successful",
        }


@pytest.mark.asyncio
async def test_resend_verification_email(client, test_user, database):
    user_in = {"email": test_user.email}

    # Verify that an unverified user can get a new email
    with mock.patch("app.api.utils.emails.send_email") as send_verification_email_mock:
        # Then, attempt to resend the verification email
        _, response = await client.post(
            f"{BASE_URL_PATH}/resend-verification-email", json=user_in
        )
        assert response.status_code == 200
        assert response.json == {
            "status": "success",
            "message": "Verification email sent",
        }

    # Verify that a verified user cannot get a new email
    test_user = database.merge(test_user)  # To prevent non persistent session error
    test_user = user_manager.update(database, test_user, {"is_email_verified": True})
    with mock.patch("app.api.utils.emails.send_email") as send_verification_email_mock:
        _, response = await client.post(
            f"{BASE_URL_PATH}/resend-verification-email",
            json={"email": test_user.email},
        )
        assert response.status_code == 200
        assert response.json == {
            "status": "success",
            "message": "Email already verified",
        }

    # Verify that an error is raised when attempting to resend the verification email for a user that doesn't exist
    with mock.patch("app.api.utils.emails.send_email") as send_verification_email_mock:
        _, response = await client.post(
            f"{BASE_URL_PATH}/resend-verification-email",
            json={"email": "invalid@example.com"},
        )
        assert response.status_code == 404
        assert response.json == {
            "status": "failure",
            "message": "Incorrect Email",
        }


@pytest.mark.asyncio
async def test_login(client, test_user, database):

    # Test for invalid credentials
    _, response = await client.post(
        f"{BASE_URL_PATH}/login",
        json={"email": "not_registered@email.com", "password": "not_registered"},
    )
    assert response.status_code == 401
    assert response.json == {
        "status": "failure",
        "message": "Invalid credentials",
    }

    # Test for unverified credentials (email)
    _, response = await client.post(
        f"{BASE_URL_PATH}/login",
        json={"email": test_user.email, "password": "testuser123"},
    )
    assert response.status_code == 401
    assert response.json == {
        "status": "failure",
        "message": "Verify your email first",
    }

    # Test for valid credentials and verified email address
    test_user = database.merge(test_user)  # To prevent non persistent session error
    test_user = user_manager.update(database, test_user, {"is_email_verified": True})
    _, response = await client.post(
        f"{BASE_URL_PATH}/login",
        json={"email": test_user.email, "password": "testuser123"},
    )
    assert response.status_code == 201
    assert response.json == {
        "status": "success",
        "message": "Login successful",
        "data": {"access": mock.ANY, "refresh": mock.ANY},
    }


@pytest.mark.asyncio
async def test_refresh_token(client, database, verified_user):

    jwt_obj = jwt_manager.create(
        database,
        {"user_id": str(verified_user.id), "access": "access", "refresh": "refresh"},
    )
    database.expunge(jwt_obj)

    # Test for invalid refresh token (not found)
    _, response = await client.post(
        f"{BASE_URL_PATH}/refresh", json={"refresh": "invalid_refresh_token"}
    )
    assert response.status_code == 404
    assert response.json == {
        "status": "failure",
        "message": "Refresh token does not exist",
    }

    # Test for invalid refresh token (invalid or expired)
    _, response = await client.post(
        f"{BASE_URL_PATH}/refresh", json={"refresh": jwt_obj.refresh}
    )
    assert response.status_code == 401
    assert response.json == {
        "status": "failure",
        "message": "Refresh token is invalid or expired",
    }

    # Test for valid refresh token
    refresh = create_refresh_token()
    jwt_obj = database.merge(jwt_obj)  # To prevent non persistent session error
    jwt_obj = jwt_manager.update(database, jwt_obj, {"refresh": refresh})
    with mock.patch("app.api.utils.tokens.verify_refresh_token") as mock_verify:
        mock_verify.return_value = True
        _, response = await client.post(
            f"{BASE_URL_PATH}/refresh", json={"refresh": jwt_obj.refresh}
        )
        assert response.status_code == 201
        assert response.json == {
            "status": "success",
            "message": "Tokens refresh successful",
            "data": {"access": mock.ANY, "refresh": mock.ANY},
        }


@pytest.mark.asyncio
async def test_get_password_otp(client, verified_user):
    email = verified_user.email

    password = "testverifieduser123"
    user_in = {"email": email, "password": password}

    with mock.patch(
        "app.api.utils.emails.send_email"
    ) as send_password_reset_email_mock:
        # Then, attempt to get password reset token
        _, response = await client.post(
            f"{BASE_URL_PATH}/request-password-reset-otp", json=user_in
        )
        assert response.status_code == 200
        assert response.json == {
            "status": "success",
            "message": "Password otp sent",
        }

    # Verify that an error is raised when attempting to get password reset token for a user that doesn't exist
    with mock.patch(
        "app.api.utils.emails.send_email"
    ) as send_password_reset_email_mock:
        _, response = await client.post(
            f"{BASE_URL_PATH}/request-password-reset-otp",
            json={"email": "invalid@example.com"},
        )
        assert response.status_code == 404
        assert response.json == {
            "status": "failure",
            "message": "Incorrect Email",
        }


@pytest.mark.asyncio
async def test_verify_password_token(client, database, verified_user):
    otp = "111111"

    # Verify that the password reset verification fails with an invalid email
    _, response = await client.post(
        f"{BASE_URL_PATH}/verify-password-reset-otp",
        json={"email": "invalidemail@example.com", "otp": otp},
    )
    assert response.status_code == 404
    assert response.json == {
        "status": "failure",
        "message": "Incorrect Email",
    }

    # Verify that the password reset verification fails with an invalid otp
    _, response = await client.post(
        f"{BASE_URL_PATH}/verify-password-reset-otp",
        json={"email": verified_user.email, "otp": otp},
    )
    assert response.status_code == 400
    assert response.json == {
        "status": "failure",
        "message": "Incorrect Otp",
    }

    # Verify that the password reset verification succeeds with a valid otp
    otp = otp_manager.create(database, {"user_id": verified_user.id}).code
    _, response = await client.post(
        f"{BASE_URL_PATH}/verify-password-reset-otp",
        json={"email": verified_user.email, "otp": otp},
    )
    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "Otp verified successfully",
    }


@pytest.mark.asyncio
async def test_reset_password(client, verified_user):
    password_reset_data = {"password": "newtestverifieduserpassword123"}

    # Verify that password reset fails if otp not yet verified
    with mock.patch(
        "app.api.utils.emails.send_email"
    ) as password_reset_success_email_mock:
        _, response = await client.post(
            f"{BASE_URL_PATH}/set-new-password", json=password_reset_data
        )
        assert response.status_code == 400
        assert response.json == {
            "status": "failure",
            "message": "Reset otp is not verified yet!",
        }

    # Verify that password reset succeeds
    with mock.patch(
        "app.api.utils.emails.send_email"
    ) as password_reset_success_email_mock:
        _, response = await client.post(
            f"{BASE_URL_PATH}/set-new-password",
            json=password_reset_data,
            cookies={"email": verified_user.email},
        )
        assert response.status_code == 200
        assert response.json == {
            "status": "success",
            "message": "Password reset successful",
        }


@pytest.mark.asyncio
async def test_logout(authorized_client):
    # Ensures if authorized user logs out successfully
    _, response = await authorized_client.get(f"{BASE_URL_PATH}/logout")

    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "message": "Logout successful",
    }

    # Ensures if unauthorized user cannot log out
    _, response = await authorized_client.get(
        f"{BASE_URL_PATH}/logout", headers={"Authorization": "invalid_token"}
    )
    assert response.status_code == 401
    assert response.json == {
        "status": "failure",
        "message": "Unauthorized user",
    }
