import logging
from .config import config

class Logger:
    def __init__(self):
        self.logger = logging.getLogger('epubdl')
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        self.handler = logging.StreamHandler()
        self.log_formatter = logging.Formatter(
            fmt="time=%(asctime)s level=%(levelname)s msg=\"%(message)s\"",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        self.handler.setFormatter(self.log_formatter)
        self.handler.setLevel(getattr(logging, config.LOG_LEVEL))
        self.logger.addHandler(self.handler)
    def info(self, msg):
        self.logger.info(msg)
    def debug(self, msg):
        self.logger.debug(msg)
    def error(self, msg):
        self.logger.error(msg)
    def warning(self, msg):
        self.logger.warning(msg)

logger = Logger()