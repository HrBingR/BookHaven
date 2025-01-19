import os
import re
import ebookmeta
from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping
from models.users import Users
from functions.db import get_session
from config.logger import logger
from config.config import config
from sqlalchemy import select

def find_epubs(base_directory):
    epubs = []
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith('.epub'):
                full_path = os.path.join(root, file)
                epubs.append(full_path)
    return epubs

def extract_metadata(epub_path, base_directory):
    book = ebookmeta.get_metadata(epub_path)
    unique_id = book.identifier or epub_path
    if re.match(r'https?://', unique_id):  # Check if it's a URL
        unique_id = re.sub(r'[^a-zA-Z0-9]', '-', unique_id)
        unique_id = re.sub(r'-+', '-', unique_id)
    title = book.title
    authors = book.author_list
    series = book.series or ''
    seriesindex = book.series_index if book.series_index is not None else 0.0
    cover_image_data = book.cover_image_data
    cover_media_type = book.cover_media_type

    relative_path = os.path.relpath(epub_path, base_directory)
    return {
        'identifier': unique_id,
        'title': title,
        'authors': authors,
        'series': series,
        'seriesindex': seriesindex,
        'relative_path': relative_path,
        'cover_image_data': cover_image_data,
        'cover_media_type': cover_media_type
    }

def remove_missing_files(session, db_identifiers, filesystem_identifiers):
    """
    Deletes database records corresponding to files missing in the filesystem, and removes the associated DB entry from ProgressMapping
    """
    missing_files = db_identifiers - filesystem_identifiers  # DB IDs not in filesystem
    if missing_files:
        filtered_results = session.query(EpubMetadata).filter(EpubMetadata.identifier.in_(missing_files)).all()
        for result in filtered_results:
            mapping_records = session.query(ProgressMapping).filter(ProgressMapping.book_id == result.id).all()
            for record in mapping_records:
                session.delete(record)
            session.delete(result)
        logger.debug(f"Removed {len(missing_files)} records from DB as the files are missing in filesystem.")

def remove_missing_user_progress(session):
    valid_users_subquery = select(Users.id)
    session.query(ProgressMapping).filter(~ProgressMapping.user_id.in_(valid_users_subquery)).delete(synchronize_session=False)

def scan_and_store_metadata(base_directory):
    session = get_session()

    try:
        # Step 1: Retrieve all current ePubs from the filesystem
        epubs = find_epubs(base_directory)
        logger.debug(f"Found {len(epubs)} ePubs in base directory: {base_directory}")

        # Step 2: Retrieve all records from the database
        all_db_records = session.query(EpubMetadata).all()
        db_identifiers = {record.identifier for record in all_db_records}

        # Step 3: Identify ePub files and process them
        filesystem_identifiers = set()
        for epub_path in epubs:
            # Extract metadata for the current ePub file
            metadata = extract_metadata(epub_path, base_directory)
            unique_id = metadata['identifier']

            filesystem_identifiers.add(unique_id)

            existing_record = session.query(EpubMetadata).filter_by(identifier=unique_id).first()

            if existing_record:
                # Update the existing record if the relative path has changed
                if existing_record.relative_path != metadata['relative_path']:
                    existing_record.relative_path = metadata['relative_path']
                    session.add(existing_record)
                    logger.debug(f"Updated relative_path in DB for identifier={unique_id}, Path: {metadata['relative_path']}")
            else:
                # Create a new entry if no record exists
                new_entry = EpubMetadata(
                    identifier=unique_id,
                    title=metadata['title'],
                    authors=', '.join(metadata['authors']),
                    series=metadata['series'],
                    seriesindex=metadata['seriesindex'],
                    relative_path=metadata['relative_path'],
                    cover_image_data=metadata['cover_image_data'],
                    cover_media_type=metadata['cover_media_type']
                )
                session.add(new_entry)
                logger.debug(f"Stored new metadata in DB for identifier={unique_id}")

        # Step 4: Find and remove database records that no longer exist in the filesystem
        if config.ENVIRONMENT != "test":
            remove_missing_files(session, db_identifiers, filesystem_identifiers)
            remove_missing_user_progress(session)

        # Commit DB changes
        session.commit()
        logger.info("Library scan and metadata update completed successfully.")

    except Exception as e:
        # Rollback DB transaction on any failure
        logger.error(f"Error during library scan and metadata update: {e}")
        session.rollback()
        raise  # Re-raise the exception for further handling by caller or logging

    finally:
        # Ensure session always closes
        logger.debug("Closing database session.")
        session.close()