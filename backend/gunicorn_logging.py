import logging
from logging.handlers import RotatingFileHandler


# Disable traceback in Gunicorn error logs
class NoStacktraceFilter(logging.Filter):
    def filter(self, record):
        # Filters out stacktraces
        return not record.exc_info


# Configure logging
gunicorn_error_logger = logging.getLogger("gunicorn.error")
gunicorn_error_logger.setLevel(logging.ERROR)

# Add a handler for errors without stacktraces
handler = RotatingFileHandler("gunicorn.log", maxBytes=100000, backupCount=10)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
handler.addFilter(NoStacktraceFilter())
gunicorn_error_logger.addHandler(handler)