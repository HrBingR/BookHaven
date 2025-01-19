def test_check_required_envs_secret_key():
    from functions.utils import check_required_envs
    from unittest.mock import patch
    with patch("config.config.config.ENVIRONMENT", "production"), \
        patch("config.config.config.SECRET_KEY", ""):
        from config.config import config
        test, message = check_required_envs(config.SECRET_KEY, config.BASE_URL)

        assert test is False
        assert message == "SECRET_KEY environment variable is not set. Generate one (bash) using: openssl rand -hex 32"

def test_check_required_envs_invalid_secret_key():
    from functions.utils import check_required_envs
    from unittest.mock import patch
    with patch("config.config.config.ENVIRONMENT", "production"), \
        patch("config.config.config.SECRET_KEY", "Hello_There"):
        from config.config import config
        test, message = check_required_envs(config.SECRET_KEY, config.BASE_URL)

        assert test is False
        assert message == "SECRET_KEY environment variable is invalid. Generate one (bash) using: openssl rand -hex 32"

def test_check_required_envs_base_url():
    from functions.utils import check_required_envs
    from unittest.mock import patch
    with patch("config.config.config.ENVIRONMENT", "production"), \
        patch("config.config.config.BASE_URL", ""):
        from config.config import config
        test, message = check_required_envs(config.SECRET_KEY, config.BASE_URL)

        assert test is False
        assert message == "BASE_URL is not set. Please set this to your application's base URL"

def test_hash_password():
    from functions.utils import hash_password
    import bcrypt

    # Test case 1: Verify hashing results in a valid BCrypt hash
    password = "123456789"
    hashed_pw = hash_password(password)

    # Check the hash starts with the correct BCrypt prefix
    assert hashed_pw.startswith("$2b$"), "Generated hash is not a valid BCrypt hash."

    # Validate the hashed password with bcrypt's `checkpw`
    assert bcrypt.checkpw(password.encode('utf-8'),
                          hashed_pw.encode('utf-8')), "Hash does not correspond to the original password."

    # Test case 2: Ensure unique hashes are generated each time
    hashed_pw_2 = hash_password(password)
    assert hashed_pw != hashed_pw_2, "Two hashes for the same password should not be identical due to salting."

    # Test case 3: Handle edge cases - empty password
    empty_hashed = hash_password("")
    assert bcrypt.checkpw(b"".decode('utf-8').encode('utf-8'), empty_hashed.encode('utf-8'))

def test_check_pw_complexity():
    from functions.utils import check_pw_complexity

    password = "P@ssw0rd"
    check_result, message = check_pw_complexity(password)

    assert check_result is True
    assert message == "Password complexity requirements have been met."

def test_check_admin_user_handles_exceptions():
    """
    Test the `check_admin_user` function to ensure it handles exceptions and returns
    the correct error responses.
    """
    from functions.utils import check_admin_user
    from unittest.mock import patch, MagicMock

    # Mock the session and force it to raise an exception
    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database exception")  # Simulate an error
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("functions.utils.get_session", mock_get_session):
        # Call the function with arbitrary valid inputs
        result, message = check_admin_user("validpassword123", "admin@example.com")

        # Verify the return values
        assert result is False, "Expected result to be False when an exception occurs."
        assert message == "Simulated database exception", "Expected the exception message to be returned."

    # Ensure the database session was closed even after an exception
    mock_session.close.assert_called_once()

def test_reset_admin_user_password_handles_exceptions():
    """
    Test the `reset_admin_user_password` function to ensure it handles exceptions and returns
    the correct error responses.
    """
    from functions.utils import reset_admin_user_password
    from unittest.mock import patch, MagicMock

    # Mock the session and force it to raise an exception
    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Simulated database exception")  # Simulate an error
    mock_get_session = MagicMock(return_value=mock_session)

    # Patch `get_session` to use the mocked session
    with patch("functions.utils.get_session", mock_get_session):
        # Call the function with arbitrary valid inputs
        result, message = reset_admin_user_password("validpassword123")

        # Verify the return values
        assert result is False, "Expected result to be False when an exception occurs."
        assert message == "Simulated database exception", "Expected the exception message to be returned."

    # Ensure the database session was closed even after an exception
    mock_session.close.assert_called_once()

def test_encrypt_totp_secret(app):
    from functions.utils import encrypt_totp_secret, decrypt_totp_secret
    with app.app_context():
        secret = "hello"
        encrypted_secret = encrypt_totp_secret(secret)
        decrypted_secret = decrypt_totp_secret(encrypted_secret)
        assert decrypted_secret == "hello"