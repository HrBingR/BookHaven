import logging
import os
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
if LOG_LEVEL not in valid_levels:
    print(f"Invalid log level '{LOG_LEVEL}', defaulting to INFO")
    LOG_LEVEL = "INFO"

class Logger:
    def __init__(self):
        self.logger = logging.getLogger('epubdl')
        self.logger.propagate = True
        if not self.logger.handlers:
            self.logger.setLevel(getattr(logging, LOG_LEVEL))
            self.handler = logging.StreamHandler()
            self.log_formatter = logging.Formatter(
                fmt="time=%(asctime)s level=%(levelname)s msg=\"%(message)s\"",
                datefmt="%Y-%m-%dT%H:%M:%S"
            )
            self.handler.setFormatter(self.log_formatter)
            self.handler.setLevel(getattr(logging, LOG_LEVEL))
            self.logger.addHandler(self.handler)
    def info(self, msg, *args):
        self.logger.info(msg, *args)
    def debug(self, msg, *args):
        self.logger.debug(msg, *args)
    def error(self, msg, *args, exc_info=None):
        if isinstance(msg, Exception):
            self.logger.error(str(msg), exc_info=msg)
        else:
            self.logger.error(msg, *args, exc_info=exc_info)
    def warning(self, msg, *args):
        self.logger.warning(msg, *args)
    def exception(self, msg, *args):
        self.logger.exception(msg, *args)

logger = Logger()