from unittest.mock import patch
import importlib
import config.logger

@patch("os.getenv", return_value="HAHAHA")
def test_logger_log_level(mockenv):
    importlib.reload(config.logger)  # Re-imports and executes the logger module
    from config.logger import LOG_LEVEL
    assert LOG_LEVEL == "INFO"  # Should now default to "INFO"

def test_logger_loggin_info(logs):
    config.logger.logger.info("INFO TEST")
    assert "INFO TEST" in logs.info

def test_logger_logging_error(logs):
    config.logger.logger.error("ERROR TEST")
    assert "ERROR TEST" in logs.error
def test_logger_logging_exception(logs):
    config.logger.logger.exception("EXCEPTION TEST")
    assert "EXCEPTION TEST" in logs.error
def test_logger_logging_error_exc_info(logs):
    try:
        raise ValueError("REAL EXCEPTION TEST")
    except ValueError as e:
        config.logger.logger.error(e)
    assert "REAL EXCEPTION TEST" in logs.error
