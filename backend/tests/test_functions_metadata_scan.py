from models.progress_mapping import ProgressMapping


def test_scan_and_store_metadata_moved(db_session):
    from functions.metadata.scan import scan_and_store_metadata
    from models.epub_metadata import EpubMetadata
    import os
    import shutil
    new_directory = "tests/epubs/test_dir"
    os.mkdir(new_directory)
    file_to_move = "tests/epubs/Pride_and_Prejudice.epub"
    shutil.move(file_to_move, new_directory)
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_file_path)
    project_root = os.path.dirname(project_root)
    scan_and_store_metadata(project_root)

    updated_record = db_session.query(EpubMetadata).filter_by(title="Pride and Prejudice").first()

    assert updated_record.relative_path == "tests/epubs/test_dir/Pride_and_Prejudice.epub"

    file_to_move = "tests/epubs/test_dir/Pride_and_Prejudice.epub"
    epubs_directory = "tests/epubs"
    shutil.move(file_to_move, epubs_directory)
    os.rmdir(new_directory)

def test_scan_and_store_metadata_deletes_missing_files(db_session):
    from functions.metadata.scan import scan_and_store_metadata
    from models.epub_metadata import EpubMetadata
    import os
    from unittest.mock import patch

    # Prepopulate database
    records = [
        EpubMetadata(
            identifier="http://test-book-7",
            title="Test Book 7",
            authors="Author Seven",
            series="Test Series 7",
            seriesindex=7.0,
            relative_path="path/to/file7.epub"
        ),
        EpubMetadata(
            id=2000,
            identifier="file8",
            title="Test Book 8",
            authors="Author Eight",
            series="Test Series 8",
            seriesindex=8.0,
            relative_path="path/to/file8.epub"
        ),
        ProgressMapping(
            id=20,
            user_id=8,
            book_id=2000,
        ),
        ProgressMapping(
            id=30,
            user_id=89,
            book_id=1
        )
    ]
    db_session.add_all(records)
    db_session.commit()

    # Mock filesystem with one file missing
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_file_path)
    project_root = os.path.dirname(project_root)

    # Patch environment to bypass the condition
    with patch("config.config.config.ENVIRONMENT", "production"):
        scan_and_store_metadata(project_root)

    # Verify 'file2' has been removed
    remaining_records = db_session.query(EpubMetadata).all()
    assert len(remaining_records) == 3
    p_and_p = db_session.query(EpubMetadata).filter_by(title="Pride and Prejudice").first()
    assert p_and_p.title == "Pride and Prejudice"
    user_id = 89
    pgmapping_result = db_session.query(ProgressMapping).filter_by(user_id=user_id).all()  # user_id = 89
    pgmapping_user_ids = [mapping.user_id for mapping in pgmapping_result]
    assert user_id not in pgmapping_user_ids

def test_scan_and_store_metadata_exception_handling():
    """
    Test the exception handling in scan_and_store_metadata.
    """
    from functions.metadata.scan import scan_and_store_metadata
    from unittest.mock import patch, MagicMock

    # Mock the session to simulate a failing database operation
    mock_session = MagicMock()
    mock_session.commit.side_effect = Exception("Simulated database failure")  # Trigger exception on commit
    mock_get_session = MagicMock(return_value=mock_session)

    # Mock the logger to track calls
    with patch("functions.metadata.scan.get_session", mock_get_session), \
            patch("functions.metadata.scan.logger.error") as mock_logger_error:

        # Perform the test (forcing an exception to occur)
        try:
            scan_and_store_metadata("/dummy/path")
        except Exception as e:
            assert str(e) == "Simulated database failure"  # Check the exception is raised as expected

        # Assert rollback was called
        mock_session.rollback.assert_called_once()

        # Assert logger.error was called at least once
        mock_logger_error.assert_called_once()

        # Extract the logged message
        logged_message = mock_logger_error.call_args[0][0]  # The full logged string

        # Verify the fully formatted message
        assert logged_message == "Error during library scan and metadata update: Simulated database failure"

    # Ensure session closes even after failure
    mock_session.close.assert_called_once()