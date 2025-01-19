from models.users import Users
from tests.conftest import db_session


def test_get_all_users(client, db_session, headers):
    """
    Test GET /api/admin/users endpoint
    """
    # Call admin endpoint
    response = client.get("/api/admin/users", headers=headers)
    users = response.json

    assert response.status_code == 200
    assert users[0]["username"] == "administrator"

def test_get_all_users_handles_exception(client, headers):
    """
    Test the `get_all_users` endpoint to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    # Mock the session and force it to raise an exception
    from unittest.mock import patch, MagicMock
    from flask import json

    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.get("/api/admin/users", headers=headers)

        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Failed to fetch users.", "Unexpected error message in the response."
        assert data["details"] == "Simulated database failure", "Unexpected exception message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_change_user_admin_status_not_admin(client, db_session, headers_non_admin):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/50/admin-status",
        json={"is_admin": True},
        headers=headers_non_admin
    )
    assert response.status_code == 403
    assert response.json["error"] == "Forbidden. Admin access only."

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=50).first()
    assert updated_user.is_admin is False

def test_change_user_admin_status_no_token(client, db_session):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/50/admin-status",
        json={"is_admin": True},
    )
    assert response.status_code == 401
    assert response.json["error"] == "Missing or invalid Authorization header."

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=50).first()
    assert updated_user.is_admin is False

def test_change_user_admin_status_expired_token(client, db_session, headers_expired):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/50/admin-status",
        json={"is_admin": True},
        headers=headers_expired
    )
    assert response.status_code == 401
    assert response.json["error"] == "Invalid or expired token."

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=50).first()
    assert updated_user.is_admin is False

def test_change_user_admin_status_invalid_is_admin(client, db_session, headers):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/50/admin-status",
        json={"is_admin": "TEST"},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json["error"] == "Invalid is_admin value provided. Must be a boolean."

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=50).first()
    assert updated_user.is_admin is False

def test_change_user_admin_status_self(client, db_session, headers):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/2/admin-status",
        json={"is_admin": False},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json["error"] == "Admins cannot remove their own admin status."

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=2).first()
    assert updated_user.is_admin is True

def test_change_user_admin_status_not_exist(client, db_session, headers):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/600/admin-status",
        json={"is_admin": True},
        headers=headers
    )
    assert response.status_code == 404
    assert response.json["error"] == "User not found."

def test_change_user_admin_status(client, db_session, headers):
    """
    Test PATCH /api/admin/users/<user_id>/admin-status endpoint
    """
    # Change admin status
    response = client.patch(
        f"/api/admin/users/50/admin-status",
        json={"is_admin": True},
        headers=headers
    )
    assert response.status_code == 200
    assert "granted" in response.json["message"]

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=50).first()
    assert updated_user.is_admin is True

def test_change_user_admin_status_exceptions(client, headers):
    """
    Test the `change_user_admin_status` endpoint to ensure it handles exceptions and returns
    the appropriate error message and status code.
    """
    # Mock the session and force it to raise an exception
    from unittest.mock import patch, MagicMock
    from flask import json

    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database failure")
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.patch(
            "/api/admin/users/50/admin-status",
            json={"is_admin": True},
            headers=headers
        )

        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Failed to update user admin status.", "Unexpected error message in the response."
        assert data["details"] == "Simulated database failure", "Unexpected exception message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_reset_user_password(client, db_session, headers):
    """
    Test POST /api/admin/users/<user_id>/reset-password endpoint
    """
    import bcrypt
    response = client.post(
        f"/api/admin/users/50/reset-password",
        json={"new_password": "PASSWORD"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["success"] is True

    # Verify change in the database
    updated_user = db_session.query(Users).filter_by(id=50).first()
    updated_user_hashed_pw = updated_user.password_hash
    assert bcrypt.checkpw("PASSWORD".encode('utf-8'),updated_user_hashed_pw.encode('utf-8'))

def test_reset_user_password_generated(client, db_session, headers):
    """
    Test POST /api/admin/users/<user_id>/reset-password endpoint
    """
    response = client.post(
        f"/api/admin/users/50/reset-password",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["new_password"] is not None

def test_reset_user_password_oidc(client, db_session, headers):
    """
    Test POST /api/admin/users/<user_id>/reset-password endpoint
    """
    response = client.post(
        f"/api/admin/users/51/reset-password",
        headers=headers
    )
    assert response.status_code == 400
    assert response.json["error"] == "Cannot reset passwords for OIDC-authenticated users."

def test_reset_user_password_not_exist(client, db_session, headers):
    """
    Test POST /api/admin/users/<user_id>/reset-password endpoint
    """
    response = client.post(
        f"/api/admin/users/600/reset-password",
        headers=headers
    )
    assert response.status_code == 404
    assert response.json["error"] == "User not found."

def test_reset_user_password_exceptions(client, headers):
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
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.post(
            "/api/admin/users/50/reset-password",
            headers=headers
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Failed to reset user password.", "Unexpected error message in the response."
        assert data["details"] == "Simulated database failure", "Unexpected exception message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_register_user(client, headers):
    response = client.post(
        "/api/admin/users/register",
        headers=headers,
        json={
            "username":"john",
            "password":"P@ssw0rd",
            "email":"john@example.com"
        }
    )

    assert response.status_code == 200
    assert "added successfully" in response.json["message"]

def test_register_user_missing_fields(client, headers):
    response = client.post(
        "/api/admin/users/register",
        headers=headers,
        json={
            "username":"john",
            "password":"P@ssw0rd"
        }
    )

    assert response.status_code == 400
    assert "field(s) are required." in response.json["error"]

def test_register_user_missing_data(client, headers):
    response = client.post(
        "/api/admin/users/register",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json["error"] == "No data submitted."

def test_register_user_invalid_password(client, headers):
    response = client.post(
        "/api/admin/users/register",
        headers=headers,
        json={
            "username":"john",
            "password":"123456",
            "email":"john@example.com"
        }
    )

    assert response.status_code == 400
    assert response.json["error"] == "Password must be at least 8 characters long."

def test_register_user_invalid_email(client, headers):
    response = client.post(
        "/api/admin/users/register",
        headers=headers,
        json={
            "username":"john",
            "password":"P@ssw0rd",
            "email":"john@examplecom"
        }
    )

    assert response.status_code == 400
    assert response.json["error"].startswith("Email validation error:")

def test_register_user_existing_username(client, headers):

    response = client.post(
        "/api/admin/users/register",
        headers=headers,
        json={
            "username":"administrator",
            "password":"P@ssw0rd",
            "email":"jenny@example.com"
        }
    )

    assert response.status_code == 400
    assert "is already registered" in response.json["error"]

def test_register_user_existing_email(client, headers):
    response = client.post(
        "/api/admin/users/register",
        headers=headers,
        json={
            "username":"jenny",
            "password":"P@ssw0rd",
            "email":"other@example.com"
        }
    )

    assert response.status_code == 400
    assert "is already registered" in response.json["error"]

def test_register_user_exceptions(client, headers):
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
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.post(
            "/api/admin/users/register",
            headers=headers,
            json={
                "username":"john",
                "password":"P@ssw0rd",
                "email":"john@example.com"
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

def test_delete_user(client, db_session, headers):
    response = client.delete(
        "/api/admin/users/54/delete",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json["message"] == "User successfully deleted."

def test_delete_user_unknown_id(client, headers):
    response = client.delete(
        "/api/admin/users/69/delete",
        headers=headers
    )

    assert response.status_code == 404
    assert response.json["error"] == "User not found."

def test_delete_user_invalid_id(client, headers):
    response = client.delete(
        "/api/admin/users/0/delete",
        headers=headers
    )

    assert response.status_code == 400
    assert response.json["error"] == "Invalid user ID."

def test_delete_user_exceptions(client, headers):
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
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.delete(
            "/api/admin/users/69/delete",
            headers=headers,
            json={
                "username":"john",
                "password":"P@ssw0rd",
                "email":"john@example.com"
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

def test_delete_user_sql_alchemy_error(client, headers):
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
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.delete(
            "/api/admin/users/69/delete",
            headers=headers,
            json={
                "username":"john",
                "password":"P@ssw0rd",
                "email":"john@example.com"
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

def test_change_email(client, headers):
    response = client.patch(
        "/api/admin/users/50/change-email",
        headers=headers,
        json={"new_email": "other6@example.com"}
    )

    assert response.status_code == 200
    assert response.json["message"] == "Email address successfully updated."

def test_change_email_no_data(client, headers):
    response = client.patch(
        "/api/admin/users/51/change-email",
        headers=headers
    )

    assert response.status_code == 400
    assert response.json["error"] == "New email address required."

def test_change_email_invalid_email(client, headers):
    response = client.patch(
        "/api/admin/users/51/change-email",
        headers=headers,
        json={"new_email": "other4@examplecom"}
    )

    assert response.status_code == 400
    assert response.json["error"].startswith("Email validation error:")

def test_change_email_invalid_user(client, headers):
    response = client.patch(
        "/api/admin/users/969/change-email",
        headers=headers,
        json={"new_email": "other5@example.com"}
    )

    assert response.status_code == 404
    assert response.json["error"] == "User not found."

def test_change_email_oidc(client, headers):
    response = client.patch(
        "/api/admin/users/51/change-email",
        headers=headers,
        json={"new_email": "other6@example.com"}
    )

    assert response.status_code == 400
    assert response.json["error"] == "Unlink OIDC before changing user's email address."

def test_change_email_exceptions(client, headers):
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
    with patch("routes.admin.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.patch(
            "/api/admin/users/50/change-email",
            headers=headers,
            json={"new_email": "other3@example.com"}
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Failed to change email address.", "Unexpected error message in the response."

    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()