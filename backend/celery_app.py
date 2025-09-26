from celery import Celery
from config.config import config
from datetime import timedelta
from config.logger import logger

def make_celery():
    celery = Celery(
        __name__,
        broker=config.redis_db_uri(1),
        backend=config.redis_db_uri(1),
        include=['functions.tasks.scan']  # Include your task modules
    )
    scan_interval = config.PERIODIC_SCAN_INTERVAL
    try:
        scan_interval = int(scan_interval)
    except ValueError:
        scan_interval = 10
    if config.SCHEDULER_ENABLED:
        celery.conf.update({
            'timezone': 'UTC',
            'enable_utc': True,
            'result_expires': timedelta(hours=24),
            'beat_schedule': {
                'scan-library-periodically': {
                    'task': 'functions.tasks.scan.scan_library_task',
                    'schedule': timedelta(minutes=scan_interval)
                },
            },
        })
    else:
        celery.conf.update({
            'timezone': 'UTC',
            'enable_utc': True,
            'result_expires': timedelta(hours=24),
        })
    return celery

celery = make_celery()

from redis import Redis
import socket
from celery.signals import worker_ready

@worker_ready.connect
def at_worker_ready(sender, **kwargs):
    # Delay import to avoid circular import
    from functions.tasks.scan import scan_library_task
    redis_lock_client = Redis.from_url(config.redis_db_uri(1))

    hostname = socket.gethostname()
    logger.info(f"Celery worker_ready signal received on host: {hostname}")

    lock = redis_lock_client.lock("startup_scan_lock", timeout=300)
    if lock.acquire(blocking=False):
        logger.info("Running initial scan on startup.")
        scan_library_task.delay()
        lock.release()
    else:
        logger.info("Startup scan already triggered elsewhere.")