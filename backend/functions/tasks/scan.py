from celery_app import celery
from functions.metadata.scan import scan_and_store_metadata
from config.config import config
from sqlalchemy.exc import SQLAlchemyError
from celery.exceptions import MaxRetriesExceededError
from config.logger import logger

@celery.task(bind=True, max_retries=5)
def scan_library_task(self):
    try:
        scan_and_store_metadata(config.BASE_DIRECTORY)
    except SQLAlchemyError as exc:
        # Check if we've exceeded retries before attempting
        if self.request.retries >= self.max_retries:
            logger.exception(
                f"Maximum retries exceeded for task '{self.name}' after {self.request.retries} attempts. "
                f"Original DB Error: {str(exc)}"
            )
            raise MaxRetriesExceededError()

        # Calculate retry delay only if within retry range
        retry_delay = 3 ** self.request.retries
        logger.warning(f"Retrying task due to database error: {str(exc)}. Attempt {self.request.retries + 1}")
        raise self.retry(exc=exc, countdown=retry_delay)