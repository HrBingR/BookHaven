def test_celery_scheduler_disabled():
    from unittest.mock import patch
    from celery_app import make_celery
    from config.config import config

    # Mock SCHEDULER_ENABLED to be False
    with patch.object(config, 'SCHEDULER_ENABLED', False):
        celery = make_celery()

        # Assert that beat_schedule is not included in the Celery configuration
        assert 'beat_schedule' not in celery.conf
        # Assert other general Celery configurations are present
        assert celery.conf['timezone'] == 'UTC'
        assert celery.conf['enable_utc'] is True
        assert 'result_expires' in celery.conf

import pytest

@pytest.mark.usefixtures("celery_app", "celery_worker")
def test_celery_scan_task_execution():
    from unittest.mock import patch
    from functions.tasks.scan import scan_library_task

    # Define the test base directory
    test_base_directory = "/fake/directory"

    # Mock `config.BASE_DIRECTORY` and `scan_and_store_metadata`
    with patch('config.config.config.BASE_DIRECTORY', test_base_directory), \
            patch('functions.tasks.scan.scan_and_store_metadata', return_value=None) as mock_scan:
        # Trigger the Celery task (this internally uses the mocked BASE_DIRECTORY)
        result = scan_library_task.apply_async().get()

        # Ensure the task completed successfully (returns None because it's mocked)
        assert result is None

        # Ensure `scan_and_store_metadata` was called with the mocked base directory
        mock_scan.assert_called_once_with(test_base_directory)

@pytest.fixture
def client():
    from flask import Flask
    from routes.scan import scan_bp
    app = Flask(__name__)
    app.register_blueprint(scan_bp)

    with app.test_client() as client:
        yield client

def test_scan_library_route(client):
    from unittest.mock import patch
    # Mock the Celery task to avoid triggering a real scan
    with patch('functions.tasks.scan.scan_library_task.delay') as mock_delay:
        response = client.post('/scan-library')

        # Check the response message
        assert response.status_code == 200
        assert response.json == {"message": "Library scan initiated."}

        # Ensure the Celery task was called
        mock_delay.assert_called_once()

from unittest.mock import patch, MagicMock
from celery.exceptions import MaxRetriesExceededError, Retry
from sqlalchemy.exc import SQLAlchemyError
from functions.tasks.scan import scan_library_task


def test_scan_library_task_retry_on_db_error():
    # Mock session.commit to raise SQLAlchemyError
    mock_session = MagicMock()
    mock_session.commit.side_effect = SQLAlchemyError("DB Error")

    # Patch `get_session` to return the mocked session
    with patch('functions.metadata.scan.get_session', return_value=mock_session), \
            patch('config.logger.logger.warning') as mock_logger_warning, \
            patch.object(scan_library_task, 'retry', side_effect=Retry()) as mock_retry:
        # Mock Celery request retries attribute
        scan_library_task.request.retries = 0  # Simulate first retry attempt

        # Call the task and confirm it retries
        with pytest.raises(Retry):  # Expect Retry exception to be raised
            scan_library_task()  # Celery injects `self` automatically

        # Verify that the logger warned about retry
        mock_logger_warning.assert_called_once_with(
            "Retrying task due to database error: DB Error. Attempt 1"
        )

        # Verify that `retry` was called
        mock_retry.assert_called_once()

@patch("celery.app.task.Task.request")
def test_scan_library_task_max_retries_exceeded(mock_request):
    # Simulate that the task is not called directly
    mock_request.called_directly = False

    # Simulate the task retry counter
    mock_request.retries = 5  # Simulate already at max retries

    # Mock session.commit to raise SQLAlchemyError
    mock_session = MagicMock()
    mock_session.commit.side_effect = SQLAlchemyError("DB Error")

    # Patch `get_session` to return the mocked session
    with patch("functions.metadata.scan.get_session", return_value=mock_session), \
            patch("config.logger.logger.exception") as mock_logger_exception:
        # Ensure retry limit is reached and MaxRetriesExceededError is raised
        with pytest.raises(MaxRetriesExceededError):  # Expect MaxRetriesExceededError
            scan_library_task()  # Let Celery handle retries automatically

        # Verify logger exception was called
        mock_logger_exception.assert_called_once_with(
            "Maximum retries exceeded for task 'functions.tasks.scan.scan_library_task' after 5 attempts. Original DB Error: DB Error"
        )