from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping

def test_get_all_books(client, db_session, headers):
    """
    Test the /api/books endpoint for returning books
    """
    # Perform GET request
    response = client.get(
        "/api/books",
        headers=headers
    )
    response_data = response.json

    assert response.status_code == 200
    assert response_data["books"][0]["title"] == "Test Book"
    assert response_data["books"][1]["title"] == "Test Book 2"

def test_get_one_book(client, db_session):
    # Test query filter
    response = client.get(
        "/api/books?query=Test Book 2",
    )
    response_data = response.json
    assert len(response_data["books"]) == 1
    assert response_data["books"][0]["title"] == "Test Book 2"

def test_get_favorites(client, db_session, headers):
    # Test query filter
    response = client.get(
        "/api/books?favorites",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["total_books"] == 1

def test_get_favorites_none(client, db_session, headers_other_user):
    # Test query filter
    response = client.get(
        "/api/books?favorites",
        headers=headers_other_user
    )
    assert response.status_code == 200
    assert response.json["message"] == "No books matching the specified query were found."

def test_get_finished(client, db_session, headers):
    # Test query filter
    response = client.get(
        "/api/books?finished",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["total_books"] == 1

def test_get_finished_favorites(client, db_session, headers_other_user):
    # Test query filter
    from datetime import datetime, timezone
    progress = ProgressMapping(
        id=600,
        user_id=50,  # Use the actual user id
        book_id=1,  # Use the actual book id
        progress="20",
        is_finished=True,
        marked_favorite=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(progress)
    db_session.commit()
    response = client.get(
        "/api/books?finished&favorites",
        headers=headers_other_user
    )
    assert response.status_code == 200
    assert response.json["total_books"] == 1

def test_get_favorites_unauthenticated(client, db_session):
    # Test query filter
    response = client.get(
        "/api/books?favorites",
    )
    assert response.status_code == 401
    assert response.json["error"] == "Unauthenticated access is not allowed"

def test_get_unknown_book(client, db_session):
    # Test empty result case
    response = client.get("/api/books?query=Unknown Book")
    response_data = response.json
    assert len(response_data["books"]) == 0

def test_get_all_books_exceptions(client, headers):
    """
    Test the `get_books` endpoint to ensure it handles exceptions and returns
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
    with patch("routes.books.get_session", mock_get_session):
        # Send a GET request to the /api/admin/users endpoint
        response = client.get(
            "/api/books",
            headers=headers
        )
        # Ensure the response is a 500 error
        assert response.status_code == 500, "Expected a 500 Internal Server Error response."

        # Parse the JSON payload
        data = json.loads(response.data)

        # Verify the error message and details in the response
        assert data["error"] == "Internal server error", "Unexpected error message in the response."
    # Ensure session was closed even after failure
    mock_session.close.assert_called_once()

def test_get_book_finished_status(client, db_session, headers):
    response = client.get(
        "/api/books",
        headers=headers
    )
    response_data = response.json

    assert response.status_code == 200
    assert response_data["books"][0]["is_finished"] == True

def test_get_book_finished_status_unauthenticated(client, db_session):
    response = client.get(
        "/api/books",
    )
    response_data = response.json

    assert response.status_code == 200
    assert response_data["books"][0]["is_finished"] == False

def test_edit_book_metadata(client, db_session, form_with_image_headers):
    """
    Test the /api/books/edit endpoint for editing book metadata
    """
    with open("tests/test.png", "rb") as image_file:
    # Perform POST request to edit metadata
        response = client.post(
            "/api/books/edit",
            data={
                "identifier": "61cee114-a920-4427-809f-50da0678c004",
                "title": "New Title",
                "authors": "New Author",
                "series": "New Series",
                "coverImage": (image_file, "test.png"),
            },
            headers=form_with_image_headers,
        )

    assert response.status_code == 200
    assert response.json["message"] == "Book metadata updated successfully"

    # Check database updates
    book = db_session.query(EpubMetadata).filter_by(identifier="61cee114-a920-4427-809f-50da0678c004").first()
    assert book.title == "New Title"
    assert book.authors == "New Author"
    assert book.series == "New Series"

def test_edit_book_metadata_series(client, db_session, form_headers):
    """
    Test the /api/books/edit endpoint for editing book metadata
    """
    # Perform POST request to edit metadata
    response = client.post(
        "/api/books/edit",
        data={
            "identifier": "61cee114-a920-4427-809f-50da0678c004",
            "seriesindex": 13.0
        },
        headers=form_headers
    )

    assert response.status_code == 200
    assert response.json["message"] == "Book metadata updated successfully"

    # Check database updates
    book = db_session.query(EpubMetadata).filter_by(identifier="61cee114-a920-4427-809f-50da0678c004").first()
    assert book.seriesindex == 13.0

def test_edit_book_metadata_invalid_series(client, db_session, form_headers):
    """
    Test the /api/books/edit endpoint for editing book metadata
    """
    # Perform POST request to edit metadata
    response = client.post(
        "/api/books/edit",
        data={
            "identifier": "61cee114-a920-4427-809f-50da0678c004",
            "seriesindex": "one"
        },
        headers=form_headers
    )

    assert response.status_code == 400
    assert response.json["error"] == "Invalid series index format"

    # Check database updates
    book = db_session.query(EpubMetadata).filter_by(identifier="61cee114-a920-4427-809f-50da0678c004").first()
    assert book.seriesindex == 13.0

def test_edit_book_metadata_not_exist(client, db_session, form_headers):
    """
    Test the /api/books/edit endpoint for editing book metadata
    """
    # Perform POST request to edit metadata
    response = client.post(
        "/api/books/edit",
        data={"identifier": "61cee114-a920-4427-809f-50ad0678c004", "title": "New Title", "authors": "New Author"},
        headers=form_headers
    )

    assert response.status_code == 404
    assert response.json["error"] == "Book not found"

def test_edit_book_metadata_unauthenticated(client, db_session):
    response = client.post(
        "/api/books/edit",
        data={"identifier": "61cee114-a920-4427-809f-50da0678c004", "title": "New Title", "authors": "New Author"},
    )

    assert response.status_code == 401
    assert response.json["error"] == "Unauthenticated access is not allowed"

def test_get_book_details_by_identifier(client, db_session, headers):
    """
    Test the /api/books/<string:book_identifier> endpoint for fetching book details
    """
    # Valid book identifier
    response = client.get("/api/books/61cee114-a920-4427-809f-50da0678c004", headers=headers)
    response_data = response.json

    assert response.status_code == 200
    assert response_data["progress"] == "20"

def test_get_book_details_by_identifier_no_progress(client, db_session, headers):
    """
    Test the /api/books/<string:book_identifier> endpoint for fetching book details
    """
    # Valid book identifier
    response = client.get("/api/books/29c52cdf-3bb8-4a69-8e36-67c865fa45e6", headers=headers)
    response_data = response.json

    assert response.status_code == 200
    assert response_data["progress"] is None

def test_get_book_details_by_identifier_unauthenticated(client, db_session):
    # Valid book identifier
    response = client.get("/api/books/61cee114-a920-4427-809f-50da0678c004")
    response_data = response.json

    assert response.status_code == 200
    assert response_data["progress"] is None

def test_get_book_details_by_unknown_identifier(client, db_session, headers):
    # Invalid book identifier
    response = client.get("/api/books/unknown_identifier", headers=headers)
    response_data = response.json

    assert response.status_code == 404
    assert response_data["error"] == "No book found with identifier unknown_identifier"

def test_update_progress_only(client, db_session, headers):
    """Test updating only the progress field"""
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"progress": "51"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["message"] == "Book progress updated successfully"

    updated_record = db_session.query(ProgressMapping).filter_by(book_id=1).first()
    assert updated_record.progress == "51"

def test_update_finished_state_only(client, db_session, headers):
    """Test updating only the finished state"""
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"is_finished": False},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["message"] == "Book progress updated successfully"

    updated_record = db_session.query(ProgressMapping).filter_by(book_id=1).first()
    assert updated_record.is_finished is False

def test_update_favorite_state_only(client, db_session, headers):
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"favorite": True},
        headers=headers
    )

    assert response.status_code == 200
    assert response.json["message"] == "Book progress updated successfully"

    updated_record = db_session.query(ProgressMapping).filter_by(book_id=1).first()
    assert updated_record.marked_favorite is True

def test_update_all_states(client, db_session, headers):
    """Test updating both progress and finished state"""
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"progress": "75", "is_finished": False, "favorite": False},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json["message"] == "Book progress updated successfully"

    updated_record = db_session.query(ProgressMapping).filter_by(book_id=1).first()
    assert updated_record.progress == "75"
    assert updated_record.is_finished is False
    assert updated_record.marked_favorite is False

def test_update_all_states_unauthenticated(client, db_session):
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"progress": "90", "is_finished": True, "favorite": True}
    )
    assert response.status_code == 401
    assert response.json["error"] == "Unauthenticated access is not allowed"

    updated_record = db_session.query(ProgressMapping).filter_by(book_id=1).first()
    assert updated_record.progress != "90"
    assert updated_record.is_finished is not True
    assert updated_record.marked_favorite is not True

def test_update_with_invalid_data(client, headers):
    """Test various invalid data scenarios"""
    # Empty JSON
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"hahaha": "haha"},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json["error"] == "Missing one of these keys in request data: 'is_finished', ', 'progress', 'favorite'"

def test_update_with_missing_data(client, headers):
    # Missing request data
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        headers=headers
    )
    assert response.status_code == 400
    assert response.json["error"] == "Missing request data"

def test_update_nonexistent_book(client, headers):
    """Test updating a book that doesn't exist"""
    response = client.put(
        "/api/books/nonexistent/progress_state",
        json={"progress": "100"},
        headers=headers
    )
    assert response.status_code == 404
    assert "error" in response.json

def test_update_invalid_token(client, headers_expired, logs):
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        headers=headers_expired
    )
    assert response.status_code == 401
    assert "error" in response.json
    assert "Invalid or expired token." in logs.debug

def test_update_invalid_user(client, headers_invalid_user, logs):
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        json={"progress": "100"},
        headers=headers_invalid_user
    )
    assert response.status_code == 401
    assert "error" in response.json
    assert "User not found." in logs.debug

def test_update_progress_new_entry(client, db_session, headers_other_user):
    response = client.put(
        "/api/books/29c52cdf-3bb8-4a69-8e36-67c865fa45e6/progress_state",
        json={"progress": "100", "is_finished": True, "favorite": False},
        headers=headers_other_user
    )
    assert response.status_code == 200
    assert response.json["message"] == "Book progress updated successfully"
    updated_record = db_session.query(ProgressMapping).filter_by(book_id=50).first()
    assert updated_record.progress == "100"
    assert updated_record.is_finished is True
    assert updated_record.marked_favorite is False

def test_update_book_progress_state_logging(client, headers):
    """
    Test that exception logging properly handles errors.
    """
    from unittest.mock import patch

    with patch("functions.book_management.logger.exception") as mock_logger:
        with patch("functions.book_management.get_session") as mock_session:
            mock_session_instance = mock_session.return_value
            mock_session_instance.commit.side_effect = Exception("Simulated failure")

            client.put(
                "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
                json={"progress": "75"},
                headers=headers
            )

            # Get the logged message
            args, _ = mock_logger.call_args

            # Assert logger was called with the correct error message
            assert args[0] == "Error occurred: %s"
            assert str(args[1]) == "Simulated failure"

def test_normal_with_totp_token(client, logs, headers_totp):
    response = client.put(
        "/api/books/61cee114-a920-4427-809f-50da0678c004/progress_state",
        headers=headers_totp
    )
    assert "TOTP token detected, marking as no_token." in logs.debug
    assert response.status_code == 401