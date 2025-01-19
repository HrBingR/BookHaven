from flask import request, jsonify
from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping
from functions.db import get_session
from models.users import Users
from config.logger import logger
from functions.auth import verify_token
from functools import wraps
from config.config import config
import inspect

def user_logged_in():
    session = get_session()
    try:
        auth_header = request.headers.get('Authorization')
        no_token = "no_token"
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            decoded_token = verify_token(token)
            if not decoded_token:
                return False, "Invalid or expired token.", no_token
            user_id = decoded_token.get("user_id")
            user_record = session.query(Users).filter_by(id=user_id).first()
            if not user_record:
                return False, "User not found.", no_token
            return True, "User token validated.", decoded_token
        return True, "Unauthenticated session in progress.", no_token
    finally:
        session.close()


def login_required(func=None, totp=False):
    """
    Decorator to check login status and enforce token type:
    - Allows optional token validation based on config.ALLOW_UNAUTHENTICATED.
    - Updates token_state if token type is invalid or missing.

    Parameters:
        func (function): The wrapped function.
        totp (bool): Set to True to allow TOTP tokens specifically for the route.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Retrieve login status and token state
            user_login_status, message, token_state = user_logged_in()
            if not user_login_status:
                logger.debug(message)
            # If unauthenticated and ALLOW_UNAUTHENTICATED=False, deny immediately
            if not config.ALLOW_UNAUTHENTICATED and token_state == "no_token":
                logger.debug("Unauthenticated access denied.")
                return jsonify({
                    "error": "Unauthenticated access is not allowed. Please see ALLOW_UNAUTHENTICATED environment variable"
                }), 401

            if totp and token_state == "no_token":
                return jsonify({
                    "error": "TOTP verification requires authentication."
                }), 401

            # Enforce token type checks when a valid token is provided
            if token_state != "no_token":
                # Extract the token type
                token_type = token_state.get("token_type", None)

                # Deny TOTP tokens unless explicitly allowed (totp=True)
                if token_type == "totp" and not totp:
                    logger.debug("TOTP token detected, marking as no_token.")
                    token_state = "no_token"

            # Pass the token state to the route if it's expecting it
            func_params = inspect.signature(func).parameters
            if 'token_state' in func_params:
                return func(*args, token_state=token_state, **kwargs)

            # Default: Run the function without token_state if not defined
            return func(*args, **kwargs)

        return wrapper

    # Allow the decorator to be used without arguments for default behavior
    if func:
        return decorator(func)
    return decorator

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