def test_serve_react_manifest(client):
    """
    Test if the manifest.json file is served correctly when it exists.
    """
    # Simulate requesting a valid static file
    response = client.get("/manifest.json")

    # If the file actually exists, we expect a successful response
    assert response.status_code == 200
    assert "application/json" in response.content_type  # Ensure correct MIME type


def test_serve_react_placeholder_image(client):
    """
    Test if a placeholder image is served correctly when it exists.
    """
    # Simulate requesting a valid static image
    response = client.get("/placeholder.jpg")

    # If the file actually exists, we expect a successful response
    assert response.status_code == 200
    assert "image/jpeg" in response.content_type  # Ensure correct MIME type


def test_serve_react_fallback_to_index(client):
    """
    Test fallback serving of index.html for unmatched paths.
    """
    # Simulate requesting a non-existent path
    response = client.get("/non-existent-route")

    # Ensure the fallback file (index.html) is served
    assert response.status_code == 200
    assert "text/html" in response.content_type  # Ensure MIME type for HTML