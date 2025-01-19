def test_login_successful(client, db_session):
    """
    Test the /login endpoint for successful login
    """
    # Send login request
    response = client.post("/login", json={
        "username": "administrator",
        "password": "P@ssw0rd"
    })

    assert response.status_code == 200
    assert "token" in response.json

def test_login_successful_email(client, db_session):
    """
    Test the /login endpoint for successful login
    """
    # Send login request
    response = client.post("/login", json={
        "username": "test@example.com",
        "password": "P@ssw0rd"
    })

    assert response.status_code == 200
    assert "token" in response.json

def test_login_totp(client, db_session):
    """
    Test the /login endpoint for successful login
    """
    # Send login request
    response = client.post("/login", json={
        "username": "totp@example.com",
        "password": "P@ssw0rd"
    })

    assert response.status_code == 200
    assert "token" in response.json

def test_login_invalid_credentials(client, db_session):
    """
    Test the /login endpoint for invalid credentials
    """
    from models.users import Users
    response = client.post("/login", json={
        "username": "administrator",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert response.json["error"] == "Invalid credentials"

    user = db_session.query(Users).filter_by(username="administrator").first()
    assert user.failed_login_count == 1

def test_login_missing_credentials(client, db_session):
    """
    Test the /login endpoint for missing credentials
    """
    response = client.post("/login", json={
        "username": "testuser"
    })

    assert response.status_code == 400
    assert response.json["error"] == "Missing username or password"

def test_login_exception(client):
    """
    Test the `login` endpoint to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    # Mock the session and force it to raise an exception
    import pytest
    from unittest.mock import patch, MagicMock
    from flask import json

    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("routes.auth.get_session", mock_get_session):
        response = client.post(
            "/login",
            json={
                "username": "administrator",
                "password": "P@ssw0rd",
            }
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Internal server error", "Unexpected error message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_otp_with_invalid_token(client):
    response = client.post(
        "/login/check-otp",
    )
    assert response.status_code == 401
    assert response.json["error"] == "TOTP verification requires authentication."

import pyotp
from datetime import datetime, timezone

def test_check_otp(app, client, db_session):
    # Step 1: Set up the user and MFA secret
    from functions.utils import encrypt_totp_secret
    from models.users import Users
    from bcrypt import hashpw, gensalt

    # Create a test user with an MFA secret
    with app.app_context():
        mfa_secret = pyotp.random_base32()
        encrypted_mfa_secret = encrypt_totp_secret(mfa_secret)

        user = db_session.query(Users).filter_by(id=49).first()
        user.mfa_secret = encrypted_mfa_secret
        user.last_used_otp = None
        db_session.commit()

        totp = pyotp.TOTP(mfa_secret)

        # Step 3: Simulate the login process to get `token_state`
        login_response = client.post('/login', json={
            'username': user.username,
            'password': 'P@ssw0rd'  # Replace with the valid password used to hash above
        })
        assert "token" in login_response.json
        assert login_response.status_code == 200

        login_token = login_response.json.get('token')
        assert login_token is not None

        # Step 4: Simulate the `check_otp` step with the valid TOTP
        headers = {"Authorization": f"Bearer {login_token}"}
        valid_otp = totp.now()
        otp_response = client.post('/login/check-otp', headers=headers, json={'otp': valid_otp})

        # Step 5: Assert successful OTP verification
        assert otp_response.status_code == 200
        otp_token = otp_response.json.get('token')
        assert otp_token is not None

        # Step 6: Test prevention of OTP reuse
        db_session.expire_all()
        db_session.refresh(user)
        second_otp_response = client.post('/login/check-otp', headers=headers, json={'otp': valid_otp})
        assert second_otp_response.status_code == 400
        assert "already been used" in second_otp_response.json['error']

        third_otp_response = client.post('/login/check-otp', headers=headers, json={'otp': '123456'})
        assert third_otp_response.status_code == 403
        assert "Incorrect one time pin" in third_otp_response.json["error"]

def test_check_no_otp(headers, client):
    otp_response = client.post('/login/check-otp', headers=headers)
    assert otp_response.json["error"] == "No one time pin submitted"

def test_check_otp_exception_handling(client, headers):
    """
    Test the `check_otp` route to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    from unittest.mock import patch, MagicMock
    from flask import json

    # Mock the session and force it to raise an exception
    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Build the token state (as required by the check_otp function)
    token_state = {"user_id": 50}

    # Patch `get_session` to use the mocked session
    with patch("routes.auth.get_session", mock_get_session):
        # Send a POST request to the /login/check-otp endpoint
        response = client.post(
            "/login/check-otp",
            headers=headers,
            json={"otp": "123456"},
            environ_base={"token_state": token_state}
        )

        # Ensure the response is a 500 Internal Server Error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Internal server error.", "Unexpected error message in the response."

    # Ensure session rollback and closure happened
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()