import pytest

@pytest.fixture
def test_app():
    from flask import Flask
    app = Flask(__name__)

    # Add minimal configuration if necessary
    app.config["TESTING"] = True  # Enables "testing mode"
    app.config["DEBUG"] = False  # Turns off debugging for tests

    yield app

def test_init_rate_limit(test_app):
    from unittest.mock import patch
    with patch("config.config.config.ENVIRONMENT", "production"):
        from config.config import config
        from functions.init import init_rate_limit
        init_rate_limit(test_app)
        assert test_app.config["RATELIMIT_ENABLED"] == config.RATE_LIMITER_ENABLED

def test_init_env_fail():
    from unittest.mock import patch
    with patch("config.config.config.BASE_URL", ""):
        from functions.init import init_env
        with pytest.raises(SystemExit) as exc:
            init_env()
        assert exc.value.code == 1

def test_init_env_exception():
    from unittest.mock import patch
    with patch("config.config.config.BASE_URL", ""):
        with patch("functions.init.check_required_envs", side_effect=Exception("Simulated exception")):
            from functions.init import init_env
            with pytest.raises(SystemExit) as exc:
                init_env()
            assert exc.value.code == 1

def test_check_admin_user(db_session):
    from functions.utils import check_admin_user

    password = ""
    email = ""
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message == "Missing admin credentials. Please set ADMIN_PASS and ADMIN_EMAIL in environment variables. These variables can be unset after initial setup."

    password = "123456"
    email = "testadmin@example.com"
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message == "Password must be at least 8 characters long."

    password = "12345678"
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message == "Password must contain at least one uppercase letter."

    password = "A1234567"
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message == "Password must contain at least one lowercase letter."

    password = "AbCdEfGh"
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message == "Password must contain at least one number."

    password = "Ab123456"
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message == "Password must contain at least one special character."

    password = "P@ssw0rd"
    email = "test@admine.$xamplecom"
    check_result, message = check_admin_user(password, email)

    assert check_result is False
    assert message.startswith("Email validation error:")

def test_init_admin_user_failed():
    from unittest.mock import patch
    from functions.init import init_admin_user
    with patch("config.config.config.ADMIN_PASS", "Pssw0rd"), \
        patch("config.config.config.ADMIN_EMAIL", "testadminy@example.com"), \
        patch("config.config.config.ENVIRONMENT", "production"):
        with pytest.raises(SystemExit) as exc:
            init_admin_user()

        assert exc.value.code == 1

def test_init_admin_user_exception():
    from unittest.mock import patch
    from functions.init import init_admin_user
    with patch("config.config.config.ADMIN_PASS", "Pssw0rd"), \
        patch("config.config.config.ADMIN_EMAIL", "testadminy@example.com"), \
        patch("config.config.config.ENVIRONMENT", "production"):
        with patch("functions.init.check_admin_user", side_effect=Exception("Simulated exception")):
            with pytest.raises(SystemExit) as exc:
                init_admin_user()
            assert exc.value.code == 1

def test_init_admin_user(db_session):
    from unittest.mock import patch
    from functions.init import init_admin_user
    from functions.utils import check_admin_user
    from models.users import Users
    with patch("config.config.config.ADMIN_PASS", "P@ssw0rd"), \
        patch("config.config.config.ADMIN_EMAIL", "testadminy@example.com"), \
        patch("config.config.config.ENVIRONMENT", "production"):
        from config.config import config
        init_admin_user()
        admin_user = db_session.query(Users).filter_by(username="admin").first()
        assert admin_user.email == "testadminy@example.com"

        check_result, message = check_admin_user(config.ADMIN_PASS, config.ADMIN_EMAIL)

        assert check_result is True
        assert message == "Admin user already exists. Skipping initial setup."

        admin_user = db_session.query(Users).filter_by(username="admin").first()
        assert admin_user.username == "admin"

def test_reset_admin_user_password_errors(db_session):
    from functions.utils import reset_admin_user_password
    from models.users import Users
    import bcrypt
    password = ""
    check_result, message = reset_admin_user_password(password)

    assert check_result is False
    assert message == "Missing password for admin user password reset. Please set ADMIN_PASS in environment variables."

    admin_user = db_session.query(Users).filter_by(username="admin").first()
    admin_user_hashed_pw = admin_user.password_hash
    password = "P@ssw0rd"
    assert bcrypt.checkpw(password.encode('utf-8'),admin_user_hashed_pw.encode('utf-8'))

    admin_user.mfa_secret = 'haha'
    admin_user.mfa_enabled = True
    db_session.commit()

    check_result, message = reset_admin_user_password(password)

    assert check_result is True
    assert message == "Admin password and MFA reset successfully."

    db_session.delete(admin_user)
    db_session.commit()

    check_result, message = reset_admin_user_password(password)

    assert check_result is False
    assert message == "Admin user not found in the database."

def test_init_admin_password_reset_fail():
    from unittest.mock import patch
    with patch("config.config.config.ADMIN_RESET", True), \
        patch("config.config.config.ADMIN_PASS", ""):
        from functions.init import init_admin_password_reset
        with pytest.raises(SystemExit) as exc:
            init_admin_password_reset()
        assert exc.value.code == 1

def test_init_admin_password_reset_exception(logs):
    from unittest.mock import patch
    with patch("config.config.config.ADMIN_RESET", True), \
        patch("config.config.config.ADMIN_PASS", ""):
        with patch("functions.init.reset_admin_user_password", side_effect=Exception("Simulated exception")):
            from functions.init import init_admin_password_reset
            init_admin_password_reset()
            assert "Failed to reset admin user password" in logs.error