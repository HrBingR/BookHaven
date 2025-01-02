import os
import ebookmeta
from models.epub_metadata import EpubMetadata
from functions.db import get_session
from config.logger import logger

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
    title = book.title
    authors = book.author_list
    series = book.series or ''
    seriesindex = book.series_index if book.series_index is not None else 0.0
    cover_image_data = book.cover_image_data
    cover_media_type = book.cover_media_type


    relative_path = os.path.relpath(epub_path, base_directory)
    return {
        'title': title,
        'authors': authors,
        'series': series,
        'seriesindex': seriesindex,
        'relative_path': relative_path,
        'cover_image_data': cover_image_data,
        'cover_media_type': cover_media_type
    }

def scan_and_store_metadata(base_directory):
    session = get_session()
    epubs = find_epubs(base_directory)
    logger.debug(f"Found {len(epubs)} epubs in base directory: {base_directory}")
    for epub_path in epubs:
        metadata = extract_metadata(epub_path, base_directory)
        cover_length = len(metadata['cover_image_data']) if metadata['cover_image_data'] else 0
        logger.debug(f"Extracted cover for {metadata['title']}: {cover_length} bytes")
        existing_record = session.query(EpubMetadata).filter_by(relative_path=metadata['relative_path']).first()
        if not existing_record:
            new_entry = EpubMetadata(
                title=metadata['title'],
                authors=', '.join(metadata['authors']),
                series=metadata['series'],
                seriesindex=metadata['seriesindex'],
                relative_path=metadata['relative_path'],
                cover_image_data=metadata['cover_image_data'],
                cover_media_type=metadata['cover_media_type']
            )
            session.add(new_entry)
            logger.debug(f"Stored new metadata in DB for relative_path={metadata['relative_path']}")

    session.commit()