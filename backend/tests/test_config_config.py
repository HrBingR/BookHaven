from config.config import str_to_bool

def test_str_to_bool():
    test_value = "False"
    result = str_to_bool(test_value)
    assert result is False

    test_value = ""
    result = str_to_bool(test_value)
    assert result is False

    test_value = 1
    result = str_to_bool(test_value)
    assert result is True

    test_value = 30
    result = str_to_bool(test_value)
    assert result is False

    test_value = "y"
    result = str_to_bool(test_value)
    assert result is True

    test_value = "Hello"
    result = str_to_bool(test_value)
    assert result is False

    test_value = True
    result = str_to_bool(test_value)
    assert result is True

def test_redis_pw():
    from unittest.mock import patch
    from config.config import Config
    config = Config()

    with patch.object(config, "REDIS_PASSWORD", "HELLO"):
        assert "HELLO" in config.redis_db_uri