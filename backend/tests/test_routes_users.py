def test_change_password(client, db_session, headers_other_user3):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user3,
        json={
            "old_password": "P@ssw0rd",
            "new_password": "P@ssw0rd1"
        }
    )

    assert response.status_code == 200
    assert response.json["message"] == "Password changed successfully."

def test_change_password_weak(client, db_session, headers_other_user3):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user3,
        json={
            "old_password": "P@ssw0rd",
            "new_password": "123456"
        }
    )

    assert response.status_code == 400
    assert response.json["error"] == "Password must be at least 8 characters long."

def test_change_password_same(client, db_session, headers_other_user3):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user3,
        json={
            "old_password": "P@ssw0rd1",
            "new_password": "P@ssw0rd1"
        }
    )

    assert response.status_code == 400
    assert response.json["error"] == "The new password cannot be the same as the current password."

def test_change_password_missing_fields(client, db_session, headers_other_user2):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user2,
        json={
            "old_password": "P@ssw0rd1"
        }
    )

    assert response.status_code == 400
    assert "field(s) are required" in response.json["error"]

def test_change_password_blank_fields(client, db_session, headers_other_user2):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user2,
        json={
            "old_password": "",
            "new_password": " "
        }
    )

    assert response.status_code == 400
    assert response.json["error"] == "Password fields cannot be empty."

def test_change_password_no_data(client, db_session, headers_other_user2):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user2
    )

    assert response.status_code == 400
    assert response.json["error"] == "No data submitted"

def test_change_password_wrong(client, db_session, headers_other_user3):
    response = client.patch(
        "/user/change-password",
        headers=headers_other_user3,
        json={
            "old_password": "hahahaha",
            "new_password": "P@ssw0rd12"
        }
    )

    assert response.status_code == 401
    assert response.json["error"] == "Current password is incorrect."

def test_change_password_invalid_user(client, db_session, headers_invalid_user):
    response = client.patch(
        "/user/change-password",
        headers=headers_invalid_user,
        json={
            "old_password": "P@ssw0rd1",
            "new_password": "P@ssw0rd12"
        }
    )

    assert response.status_code == 401
    assert response.json["error"] == "Unauthenticated access is not allowed"

def test_change_password_exceptions(client, headers):
    """
    Test the `reset_user_password` endpoint to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    # Mock the session and force it to raise an exception
    from unittest.mock import patch, MagicMock
    from flask import json

    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("routes.users.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.patch(
            "/user/change-password",
            headers=headers,
            json={
                "old_password": "P@ssw0rd1",
                "new_password": "P@ssw0rd123"
            }
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "An unexpected error occurred. Please try again later.", "Unexpected error message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_change_password_sql_alchemy_error(client, headers):
    """
    Test the `reset_user_password` endpoint to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    # Mock the session and force it to raise an exception
    from unittest.mock import patch, MagicMock
    from flask import json
    from sqlalchemy.exc import SQLAlchemyError

    mock_session = MagicMock()
    mock_session.query.side_effect = SQLAlchemyError("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("routes.users.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.patch(
            "/user/change-password",
            headers=headers,
            json={
                "old_password": "P@ssw0rd1",
                "new_password": "P@ssw0rd123"
            }
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "An unexpected database error occurred. Please try again later.", "Unexpected error message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_enable_mfa_other_user2(app, client, db_session):
    from models.users import Users
    import pyotp

    # Step 1: Update the test user (other_user2) to ensure initial state for the test
    with app.app_context():
        other_user2 = db_session.query(Users).filter_by(id=53).first()
        assert other_user2 is not None  # Ensure user exists
        other_user2.mfa_enabled = False
        other_user2.mfa_secret = None
        db_session.commit()

        # Step 2: Log in as other_user2 to obtain a valid token
        login_response = client.post('/login', json={
            'username': other_user2.username,
            'password': 'P@ssw0rd1'  # Replace this with the test password
        })
        assert login_response.status_code == 200
        assert "token" in login_response.json
        login_token = login_response.json.get("token")

        # Step 3: Call `enable_mfa` endpoint with the login token
        headers = {"Authorization": f"Bearer {login_token}"}
        enable_mfa_response = client.post('/user/enable-mfa', headers=headers)

        # Step 4: Validate the response for successful MFA enablement
        assert enable_mfa_response.status_code == 200
        response_data = enable_mfa_response.json
        assert response_data["message"] == "MFA Successfully Enabled"
        assert "totp_provisioning_url" in response_data
        assert "mfa_secret" in response_data

        # Step 5: Validate user MFA fields in the database
        db_session.expire_all()
        db_session.refresh(other_user2)
        assert other_user2.mfa_enabled is True
        assert other_user2.mfa_secret is not None

        # Step 6: Make sure the user cannot enable MFA again
        duplicate_mfa_response = client.post('/user/enable-mfa', headers=headers)
        assert duplicate_mfa_response.status_code == 400
        assert duplicate_mfa_response.json["error"] == "User already has MFA enabled."

        # Step 7: Test unauthenticated access
        unauthenticated_response = client.post('/user/enable-mfa')
        assert unauthenticated_response.status_code == 401
        assert unauthenticated_response.json["error"] == "Unauthenticated access is not allowed"

def test_enable_mfa_exceptions(client, headers):
    """
    Test the `reset_user_password` endpoint to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    # Mock the session and force it to raise an exception
    from unittest.mock import patch, MagicMock
    from flask import json

    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("routes.users.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.post(
            "/user/enable-mfa",
            headers=headers
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "An unexpected error occurred", "Unexpected error message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()