from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping
from functions.db import get_session
from models.users import Users
from config.logger import logger

def generate_session_id():
    import uuid
    return str(uuid.uuid4())


def get_book_progress_record(token_user_id, book_identifier, session):
    user = session.query(Users).filter_by(id=token_user_id).first()
    book = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
    if not session.query(ProgressMapping).filter_by(user_id=user.id, book_id=book.id).first():
        return False, None
    progress_record = session.query(ProgressMapping).filter_by(user_id=user.id, book_id=book.id).first()
    return True, progress_record


def get_book_progress(token_state, book_identifier, session):
    token_user_id = token_state.get("user_id")
    book_progress_status, book_progress = get_book_progress_record(token_user_id, book_identifier, session)
    if not book_progress_status:
        return False, None
    return True, book_progress

def construct_new_book_progress_record(data):
    record = {}
    if 'is_finished' in data:
        record['is_finished'] = bool(data['is_finished'])
    if 'progress' in data:
        record['progress'] = str(data['progress'])
    if 'favorite' in data:
        record['marked_favorite'] = bool(data['favorite'])
    return record


def update_book_progress_state(token_state, book_identifier, data):
    token_user_id = token_state.get("user_id")
    session = get_session()
    record_status, record = get_book_progress_record(token_user_id, book_identifier, session)
    try:
        if not record_status:
            user = session.query(Users).filter_by(id=token_user_id).first()
            book = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
            logger.debug(f"Book identifier: {book.identifier}")
            if user and book:
                progress_record = construct_new_book_progress_record(data)
                updated_state = ProgressMapping(user_id=user.id, book_id=book.id, **progress_record)
                session.add(updated_state)
                session.commit()
                return True, "Book progress updated successfully"
        if 'is_finished' in data:
            finished_state = data['is_finished']
            record.is_finished = bool(finished_state)
            session.commit()
        if 'progress' in data:
            progress_state = data['progress']
            record.progress = progress_state
            session.commit()
        if 'favorite' in data:
            favorite_state = data['favorite']
            record.marked_favorite = favorite_state
            session.commit()
        return True, "Book progress updated successfully"
    except Exception as e:
        session.rollback()
        logger.exception("Error occurred: %s", e)
        return False, f"Error updating finished state: {str(e)}"
    finally:
        session.close()
