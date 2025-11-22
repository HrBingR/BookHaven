import os
import re
import ebookmeta
import secrets
import hashlib
from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping
from models.users import Users
from functions.db import get_session
from config.logger import logger
from config.config import config
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from tempfile import NamedTemporaryFile
import pyvips
from functions.utils import update_redis_cache, invalidate_redis_cache


def find_epubs(base_directory):
    epubs = []
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith('.epub'):
                full_path = os.path.join(root, file)
                epubs.append(full_path)
    return epubs


def get_metadata(epub_path, base_directory):
    book_meta = extract_metadata(epub_path)
    relative_path = os.path.relpath(epub_path, base_directory)
    raw_id = (book_meta['identifier'] or "").strip()
    if not raw_id:
        filename = os.path.basename(epub_path)
        unique_id = os.path.splitext(filename)[0]
    elif re.match(r'https?://', raw_id):
        unique_id = re.sub(r'[^a-zA-Z0-9]', '-', raw_id)
        unique_id = re.sub(r'-+', '-', unique_id)
    else:
        unique_id = raw_id
    cover_image_token = secrets.token_urlsafe(12)[:16]
    cover_image_path = get_image_save_path(cover_image_token) if book_meta['cover_image_data'] is not None else None

    return {
        'identifier': unique_id,
        'title': book_meta['title'],
        'authors': book_meta['authors'],
        'series': book_meta['series'],
        'seriesindex': book_meta['seriesindex'],
        'relative_path': relative_path,
        'cover_image_data': book_meta['cover_image_data'],
        'cover_image_path': cover_image_path
    }


def make_cover_webp_vips(src_bytes: bytes, target_max_height: int = 300, quality: int = 78) -> bytes:
    """
    Convert image bytes to a WebP cover:
    - sRGB, no alpha (flattened to white)
    - height <= target_max_height, aspect preserved, no upscaling
    - metadata stripped
    """
    # Stream from memory
    img = pyvips.Image.new_from_buffer(src_bytes, "", access="sequential")

    # Flatten any alpha onto white (even if you don't expect it, this is cheap and safe)
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Ensure sRGB/GRAY
    try:
        if img.interpretation not in ("srgb", "grey"):
            img = img.colourspace("srgb")
    except pyvips.Error:
        # Fallback in odd color profiles
        img = img.colourspace("srgb")

    # Resize with height cap (no upscaling)
    if img.height > target_max_height:
        scale = target_max_height / float(img.height)
        img = img.resize(scale)

    # Save to WebP buffer
    webp_bytes = img.webpsave_buffer(
        Q=quality,       # ~75–80 is a good default
        lossless=False,  # lossy typically best for covers
        effort=6,        # higher = more CPU, smaller output (0–6)
        strip=True       # drop metadata/icc to keep it small
    )
    return webp_bytes


def get_image_save_path(token):
    ext = ".webp"
    filename = f"{token}{ext}"
    cover_base_path = config.COVER_BASE_DIRECTORY
    digest = hashlib.blake2b(token.encode('ascii'), digest_size=config.COVER_DIRECTORY_LEVELS).digest()
    parts = tuple(str(b % config.COVER_DIRECTORIES_PER_LEVEL) for b in digest)
    full_path = cover_base_path.joinpath(*parts, filename)
    relative_path = full_path.relative_to(cover_base_path)
    return relative_path


def extract_metadata(epub_path):

    book = ebookmeta.get_metadata(epub_path)
    book_meta = {
        'identifier' : book.identifier,
        'title' : book.title,
        'authors' : book.author_list,
        'series' : book.series or '',
        'seriesindex' : float(book.series_index) if book.series_index is not None else 0.0,
        'cover_image_data' : book.cover_image_data
    }
    return book_meta


def remove_missing_files(session, db_identifiers, filesystem_identifiers):
    """
    Deletes database records corresponding to files missing in the filesystem, and removes the associated DB entry from ProgressMapping.
    Excludes manually uploaded files by checking if they exist in the uploads directory.
    """
    missing_files = db_identifiers - filesystem_identifiers
    if missing_files:
        filtered_results = session.query(EpubMetadata).filter(EpubMetadata.identifier.in_(missing_files)).all()
        files_to_delete = []
        uploaded_files_skipped = 0
        for result in filtered_results:
            full_path = os.path.join(config.BASE_DIRECTORY, result.relative_path)
            if os.path.exists(full_path):
                uploaded_files_skipped += 1
                logger.debug(
                    f"Skipping deletion of existing file not found in scan: {result.identifier} (path: {result.relative_path})")
                continue
            files_to_delete.append(result)
        for result in files_to_delete:
            mapping_records = session.query(ProgressMapping).filter(ProgressMapping.book_id == result.id).all()
            for record in mapping_records:
                session.delete(record)
            session.delete(result)
            invalidate_redis_cache(result.identifier)
        if files_to_delete:
            logger.debug(
                f"Removed {len(files_to_delete)} records from DB as the files are truly missing from filesystem.")
        if uploaded_files_skipped > 0:
            logger.debug(
                f"Skipped deletion of {uploaded_files_skipped} files that exist but weren't found in filesystem scan.")


def remove_missing_user_progress(session):
    valid_users_subquery = select(Users.id)
    session.query(ProgressMapping).filter(~ProgressMapping.user_id.in_(valid_users_subquery)).delete(synchronize_session=False)


def add_new_db_entry(session, unique_id, metadata):
    fallback_identifier = unique_id.strip() or metadata['relative_path']
    cover_image_path = metadata['cover_image_path'].as_posix() if metadata['cover_image_path'] is not None else None
    new_entry = EpubMetadata(
        identifier=fallback_identifier,
        title=metadata['title'],
        authors=', '.join(metadata['authors']),
        series=metadata['series'],
        seriesindex=metadata['seriesindex'],
        relative_path=metadata['relative_path'],
        cover_image_path=cover_image_path
    )
    session.add(new_entry)
    try:
        session.flush()
        logger.debug(f"Stored new metadata in DB for identifier={new_entry.identifier}")
        return True
    except IntegrityError:
        logger.warning(f"Duplicate entry skipped for identifier={unique_id}")
        session.rollback()
        return False


def save_cover_image(cover_image_data, cover_image_path):
    path = config.COVER_BASE_DIRECTORY.joinpath(cover_image_path)
    webp_bytes = make_cover_webp_vips(cover_image_data)
    path.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile("wb", delete=False, dir=path.parent) as tmp:
        tmp.write(webp_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    try:
        os.replace(tmp_name, path)
    except Exception as e:
        logger.error(f"Error writing cover image to '{path}': {e}")
        try:
            os.remove(tmp_name)
        except OSError as e:
            logger.error(f"Error during temporary file cleanup: {e}")
            pass
        raise


def scan_and_store_metadata(base_directory, source="default"):
    session = get_session()
    try:
        epubs = find_epubs(base_directory)
        logger.debug(f"Found {len(epubs)} ePubs in base directory: {base_directory}")
        all_db_records = session.query(EpubMetadata).all()
        db_identifiers = {record.identifier for record in all_db_records}
        filesystem_identifiers = set()
        for epub_path in epubs:
            metadata = get_metadata(epub_path, base_directory)
            unique_id = metadata['identifier']
            logger.debug(f"Book Title: {metadata['title']}")
            filesystem_identifiers.add(unique_id)
            existing_record = session.query(EpubMetadata).filter_by(identifier=unique_id).first()
            if existing_record:
                if source == "init":
                    update_redis_cache(metadata)
                if existing_record.relative_path != metadata['relative_path']:
                    existing_record.relative_path = metadata['relative_path']
                    session.add(existing_record)
                    update_redis_cache(metadata)
                    logger.debug(f"Updated relative_path in DB for identifier={unique_id}, Path: {metadata['relative_path']}")
            else:
                if add_new_db_entry(session, unique_id, metadata):
                    if metadata['cover_image_path'] is not None:
                        save_cover_image(metadata['cover_image_data'], metadata['cover_image_path'])
                        update_redis_cache(metadata)
        if config.ENVIRONMENT != "test":
            remove_missing_files(session, db_identifiers, filesystem_identifiers)
            remove_missing_user_progress(session)
        session.commit()
        logger.info("Library scan and metadata update completed successfully.")
    except Exception as e:
        logger.error(f"Error during library scan and metadata update: {e}")
        session.rollback()
    finally:
        logger.debug("Closing database session.")
        session.close()
