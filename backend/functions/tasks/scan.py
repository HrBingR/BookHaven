from redis import Redis
from celery_app import celery
from celery.exceptions import MaxRetriesExceededError
from config.config import config
from config.logger import logger
from sqlalchemy.exc import SQLAlchemyError
from functions.metadata.scan import scan_and_store_metadata

logger.info(f"REDIS LOCK URI: {config.REDIS_LOCK_DB_URI}")
redis_lock_client = Redis.from_url(config.REDIS_LOCK_DB_URI)

@celery.task(bind=True, name="functions.tasks.scan.scan_library_task", max_retries=5)
def scan_library_task(self):
    lock = redis_lock_client.lock("scan_lock", timeout=900)  # e.g., 15-minute hard max timeout
    if not lock.acquire(blocking=False):
        logger.warning("Another scan is already running. Skipping this one.")
        return "scan_already_running"
    try:
        logger.info("Starting scan with lock acquired.")
        scan_and_store_metadata(config.BASE_DIRECTORY)
        return "scan_completed"
    except SQLAlchemyError as exc:
        if self.request.retries >= self.max_retries:
            logger.exception(f"Max retries exceeded after {self.request.retries} attempts. DB Error: {str(exc)}")
            raise MaxRetriesExceededError()
        retry_delay = 3 ** self.request.retries
        logger.warning(f"Retrying due to DB error: {str(exc)} (attempt {self.request.retries + 1})")
        raise self.retry(exc=exc, countdown=retry_delay)
    finally:
        lock.release()
        logger.info("Scan complete. Lock released.")
