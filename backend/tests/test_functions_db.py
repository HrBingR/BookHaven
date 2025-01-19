from unittest.mock import patch
import pytest

@patch("config.config.config.DB_TYPE", "mysql")  # Patch the DB_TYPE directly
def test_get_database_url_mysql():
    from functions.db import get_database_url
    url = get_database_url()
    assert url.startswith("mysql+pymysql://")  # Ensure the URL uses MySQL format

@patch("config.config.config.DB_TYPE", "postgres")  # Patch the DB_TYPE directly
def test_get_database_url_postgres():
    from functions.db import get_database_url
    url = get_database_url()
    assert url.startswith("postgresql://")  # Ensure the URL uses MySQL format

@patch("config.config.config.DB_TYPE", "sqlite")  # Patch the DB_TYPE directly
def test_get_database_url_sqlite():
    from functions.db import get_database_url
    url = get_database_url()
    assert url.startswith("sqlite:///")  # Ensure the URL uses MySQL format

@patch("config.config.config.DB_TYPE", "unknown")  # Patch the DB_TYPE to an unsupported value
def test_get_database_url_invalid_db_type():
    from functions.db import get_database_url

    # Use pytest.raises to catch the ValueError
    with pytest.raises(ValueError, match="Unsupported DB_TYPE: unknown"):
        get_database_url()