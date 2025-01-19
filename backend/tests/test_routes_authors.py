from email.encoders import encode_7or8bit
from unittest.mock import patch


def test_get_authors_no_books(client):
    """
    Test /api/authors when there are no books in the database (total_books == 0).
    """
    from unittest.mock import patch
    with patch("routes.authors.get_session") as mock_get_session:
        # Mock the session
        mock_session = mock_get_session.return_value
        mock_session.query.return_value.count.return_value = 0

        # Make a GET request to the endpoint
        response = client.get("/api/authors")

        # Verify the status code and response
        assert response.status_code == 200
        assert response.json == {
            "authors": [],
            "total_authors": 0
        }

def test_get_authors(client, headers):
    """
    Test the /api/authors endpoint for returning books
    """
    # Perform GET request
    response = client.get(
        "/api/authors",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json["total_authors"] != 0

def test_get_authors_no_auth(client):
    """
    Test the /api/authors endpoint for returning books
    """
    from unittest.mock import patch
    with patch("config.config.config.ALLOW_UNAUTHENTICATED", False):
        # Perform GET request
        response = client.get("/api/authors")
        assert response.status_code == 401
        assert response.json["error"] == "Unauthenticated access is not allowed. Please see ALLOW_UNAUTHENTICATED environment variable"

def test_get_author_books(client):
    from urllib.parse import quote
    encoded_author = quote("Jane Austen")
    response = client.get(f"/api/authors/{encoded_author}",)

    assert response.status_code == 200
    assert response.json["total_books"] == 1

def test_get_author_books_not_exist(client):
    from urllib.parse import quote
    encoded_author = quote("Jane Austin")
    response = client.get(f"/api/authors/{encoded_author}",)

    assert response.status_code == 404
    assert "No books found for author" in response.json["error"]