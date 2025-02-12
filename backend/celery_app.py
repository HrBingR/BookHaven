from celery import Celery
from config.config import config
from datetime import timedelta

def make_celery():
    celery = Celery(
        __name__,
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
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