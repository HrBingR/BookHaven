from models.epub_metadata import EpubMetadata

def test_get_cover_with_cover_image(client):
    """
    Test that a valid book with a cover image returns the correct image data and MIME type.
    """
    # Make request for the cover of an existing book (real endpoint)
    response = client.get("/api/covers/http-www-gutenberg-org-1342")

    # Validate response
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/jpeg"  # Ensure the MIME type is JPEG
    assert len(response.data) > 0  # Ensure image data is returned (non-empty binary data)

def test_get_cover_without_cover_image(client):
    """
    Test that a book without a cover image serves the placeholder image.
    """
    # Simulate an identifier for a book without a cover (non-existent ID in the database)
    import os
    response = client.get("/api/covers/nonexistent1234")

    # Validate response
    assert response.status_code == 200

    # Ensure the placeholder image is served
    placeholder_path = os.path.join(client.application.static_folder, "placeholder.jpg")
    with open(placeholder_path, "rb") as f:
        placeholder_data = f.read()
    assert response.data == placeholder_data  # Validate it's indeed the placeholder image
    assert response.headers["Content-Type"] == "image/jpeg"  # Validate the MIME type is still JPEG

def test_download_valid_book(client):
    """
    Test downloading a book with a valid identifier that exists in the database and filesystem.
    """
    import os
    from unittest.mock import patch

    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_file_path)
    project_root = os.path.dirname(project_root)

    with patch("config.config.config.BASE_DIRECTORY", project_root):
        response = client.get("/download/61cee114-a920-4427-809f-50da0678c004")

    # Assert
    assert response.status_code == 200
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert response.content_type == "application/epub+zip"

    # Reading the file to check content
    epub_path = os.path.join("tests", "epubs", "Test Book - Author One.epub")
    with open(epub_path, "rb") as f:
        expected_file_data = f.read()

    assert response.data == expected_file_data  # Confirm file content matches

def test_download_book_not_in_database(client):
    """
    Test downloading a book with an identifier that does not exist in the database.
    """
    # Act
    response = client.get("/download/61cee114-a920-4427-809f-50ad7678c004")

    # Assert
    assert response.status_code == 404
    assert b"Resource not found" in response.data

def test_download_file_missing(client, headers_media_test):
    """
    Test downloading a book that exists in the database but is missing in the filesystem.
    """
    import os
    import shutil
    book_identifier = "61cee114-a920-4427-809f-50da0678c004"
    epub_path = os.path.join("tests", "epubs", "Test Book - Author One.epub")
    tmp_directory = os.path.join("tests", "epubs", "tmp_test_dir")

    try:
        # Move file to simulate a missing file
        os.mkdir(tmp_directory)
        shutil.move(epub_path, tmp_directory)

        # Act
        response = client.get(
            f"/download/{book_identifier}",
            headers=headers_media_test
        )

        # Assert
        assert response.status_code == 404
        assert b"Not Found" in response.data
    finally:
        # Clean up: Move file back and remove temporary directory
        shutil.move(os.path.join(tmp_directory, "Test Book - Author One.epub"), "tests/epubs")
        os.rmdir(tmp_directory)

def test_stream_valid_book(client):
    """
    Test streaming a book with a valid identifier that exists in the database and filesystem,
    and indirectly test `serve_book_file` by following the returned URL.
    """
    import os
    from unittest.mock import patch

    # The valid book identifier (as used in `test_download_valid_book`)
    book_identifier = "61cee114-a920-4427-809f-50da0678c004"

    # Get the current project root as in other tests
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_file_path)
    project_root = os.path.dirname(project_root)

    # Patch the BASE_DIRECTORY to set up the file system correctly
    with patch("config.config.config.BASE_DIRECTORY", project_root):
        # Act: Make request to `stream` endpoint
        from config.config import config
        response = client.get(f"/stream/{book_identifier}")

        # Assert: The `stream` endpoint responds as expected
        assert response.status_code == 200
        response_json = response.get_json()
        assert "url" in response_json  # Ensure `url` exists in the JSON
        epub_file_url = response_json["url"]
        assert epub_file_url.startswith(config.BASE_URL.rstrip("/"))

        # Act: Make a follow-up request to the generated URL (indirectly testing `serve_book_file`)
        epub_relative_path = epub_file_url.split("/files/")[-1]  # Extract path after `/files/`
        serve_response = client.get(f"/files/{epub_relative_path}")

        # Assert: The `serve_book_file` endpoint responds as expected
        assert serve_response.status_code == 200
        assert serve_response.headers["Content-Disposition"].startswith("inline;")
        assert serve_response.content_type == "application/epub+zip"

        # Validate that the correct file is served
        epub_path = os.path.join("tests", "epubs", "Test Book - Author One.epub")
        with open(epub_path, "rb") as f:
            expected_file_data = f.read()

        assert serve_response.data == expected_file_data  # Confirm file content matches

def test_stream_missing_db_record(client):
    """
    Test streaming a book with a missing database entry, expecting a 404 response.
    """
    # Act: Make a request with a non-existent book identifier
    response = client.get("/stream/nonexistent-book-id")

    # Assert: Check for 404 response and error message
    assert response.status_code == 404
    assert b"Book not found." in response.data

def test_stream_missing_file(client, headers_media_test):
    """
    Test streaming a book with a valid database entry but missing file, expecting a 404 response.
    """
    import os
    import shutil

    book_identifier = "61cee114-a920-4427-809f-50da0678c004"  # Valid book ID
    epub_path = os.path.join("tests", "epubs", "Test Book - Author One.epub")
    tmp_directory = os.path.join("tests", "epubs", "tmp_test_dir")

    try:
        # Move the file to simulate it being missing
        os.mkdir(tmp_directory)
        shutil.move(epub_path, tmp_directory)

        # Act: Make the streaming request
        response = client.get(
            f"/stream/{book_identifier}",
            headers=headers_media_test
        )

        # Assert: Check for 404 response and correct error message
        assert response.status_code == 404
        assert b"ePub file not found." in response.data
    finally:
        # Clean up: Move the file back to its original location
        shutil.move(os.path.join(tmp_directory, "Test Book - Author One.epub"), epub_path)
        os.rmdir(tmp_directory)

def test_serve_book_file_missing_file(client, headers_media_test):
    """
    Test directly calling `serve_book_file` with a non-existent file, expecting a 404 response.
    """
    # Act: Make a request to the `serve_book_file` endpoint with a missing file
    response = client.get(
        "/files/nonexistent.epub",
        headers=headers_media_test
    )

    # Assert: Check for 404 response and appropriate error message
    assert response.status_code == 404
    assert b"File not found." in response.data