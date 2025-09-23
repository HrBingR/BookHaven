from sqlalchemy import or_, and_
from flask import Blueprint, request, jsonify, url_for, current_app
from sqlalchemy.exc import IntegrityError
from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping
from models.users import Users
from models.requests import Requests
from functions.db import get_session
from functions.book_management import get_book_progress, update_book_progress_state
from functions.roles import login_required
from config.config import config, str_to_bool
from config.logger import logger
import ebookmeta
import os
import base64
from functions.metadata.scan import get_metadata, add_new_db_entry
from urllib.parse import unquote

books_bp = Blueprint('books', __name__)


@books_bp.route('/api/books', methods=['GET'])
@login_required
def get_books(token_state):
    """
    Returns a JSON response of books with optional search and pagination.

    If 'favorites' is a query parameter, limits results to only those books
    marked as a favorite for the logged-in user. Can combine with 'query' filter.
    """
    query = request.args.get('query', '', type=str)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 18, type=int)
    favorites_queried = str_to_bool(request.args.get('favorites', False))
    finished_queried = str_to_bool(request.args.get('finished', False))
    unfinished_queried = str_to_bool(request.args.get('unfinished', False))
    session = get_session()
    try:
        books_query = session.query(EpubMetadata)
        if favorites_queried is True or finished_queried is True or unfinished_queried is True:
            if token_state == "no_token":
                return jsonify({"error": "Unauthenticated access is not allowed"}), 401
            user_id = token_state["user_id"]
            books_query_favorite = (
                books_query.join(ProgressMapping, ProgressMapping.book_id == EpubMetadata.id)
                .filter(
                    ProgressMapping.user_id == user_id,
                    ProgressMapping.marked_favorite.is_(True)
                )
            )
            books_query_finished = (
                books_query.join(ProgressMapping, ProgressMapping.book_id == EpubMetadata.id)
                .filter(
                    ProgressMapping.user_id == user_id,
                    ProgressMapping.is_finished.is_(True)
                )
            )
            books_query_unfinished = (
                books_query
                .outerjoin(
                    ProgressMapping,
                    and_(ProgressMapping.book_id == EpubMetadata.id, ProgressMapping.user_id == user_id)
                )
                .filter(
                    or_(
                        ProgressMapping.is_finished.is_(False),
                        ProgressMapping.id.is_(None)
                    )
                )
            )
            if favorites_queried is True and finished_queried is True:
                books_query = books_query_favorite.union(books_query_finished)
            elif favorites_queried is True and unfinished_queried is True:
                books_query = books_query_favorite.union(books_query_unfinished)
            elif favorites_queried is True:
                books_query = books_query_favorite
            elif finished_queried is True:
                books_query = books_query_finished
            elif unfinished_queried is True:
                books_query = books_query_unfinished
            if books_query.count() == 0:
                return jsonify({"message": "No books matching the specified query were found."}), 200
        if query:
            query_like = f"%{query}%"
            books_query = books_query.filter(
                (EpubMetadata.title.ilike(query_like)) |
                (EpubMetadata.authors.ilike(query_like)) |
                (EpubMetadata.series.ilike(query_like))
            )
        books_query = books_query.order_by(
            EpubMetadata.authors,
            EpubMetadata.series,
            EpubMetadata.seriesindex,
            EpubMetadata.title
        )
        total_books = books_query.count()
        books = books_query.offset(offset).limit(limit).all()
        book_list = []
        for book in books:
            book_progress_finished = False
            book_progress_favorite = False
            if token_state != "no_token":
                book_progress_status, book_progress = get_book_progress(token_state, book.identifier, session)
                if book_progress_status:
                    book_progress_finished = book_progress.is_finished
                    book_progress_favorite = book_progress.marked_favorite
            book_list.append({
                "id": book.id,
                "title": book.title,
                "authors": book.authors.split(", "),
                "series": book.series,
                "seriesindex": book.seriesindex,
                "coverUrl": f"/api/covers/{book.identifier}",
                "relative_path": book.relative_path,
                "identifier": book.identifier,
                "is_finished": book_progress_finished,
                "marked_favorite": book_progress_favorite,
            })
        return jsonify({
            "books": book_list,
            "total_books": total_books,
            "fetched_offset": offset,
            "next_offset": offset + limit,
            "remaining_books": max(0, total_books - (offset + limit))
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()


@books_bp.route('/api/books/upload', methods=['POST'])
@login_required(required_roles=["admin", "editor"])
def upload_file(token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    """
    Handle file upload.
    Validates file extension and checks for existing files/DB references.
    """
    if not current_app.config['UPLOADS_ENABLED']:
        return jsonify({'error': 'Uploads feature is disabled'}), 418
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.lower().endswith('.epub'):
            return jsonify({'error': 'Only .epub files are allowed'}), 400
        filename = file.filename
        existing_upload_files = []
        existing_basedir_files = []
        for root, dirs, files in os.walk(config.BASE_DIRECTORY):
            existing_basedir_files.extend([f.lower() for f in files if f.endswith('.epub')])
        for root, dirs, files in os.walk(config.UPLOADS_DIRECTORY):
            existing_upload_files.extend([f.lower() for f in files if f.endswith('.epub')])
        if filename.lower() in existing_basedir_files:
            return jsonify({
                'error': 'A file with this name already exists in the library',
                'filename': filename
            }), 409
        if filename.lower() in existing_upload_files:
            return jsonify({
                'error': 'A file with this name already exists in the library',
                'filename': filename
            }), 409
        file_filepath = os.path.join(config.UPLOADS_DIRECTORY, filename)
        file.save(file_filepath)
        logger.info(f"Save filename: {file_filepath}")
        logger.info(f"Base directory: {config.BASE_DIRECTORY}")
        new_filepath = os.path.join(config.BASE_DIRECTORY, "_uploads", filename)
        book_metadata = get_metadata(new_filepath, config.BASE_DIRECTORY)
        session = get_session()
        book_record = session.query(EpubMetadata).filter_by(identifier=str(book_metadata['identifier'])).first()
        if book_record:
            return jsonify({
                'error': 'A book with this identifier already exists in the library',
            }), 409
        session.close()
        logger.info("File uploaded successfully")
        cover_image_base64 = None
        has_cover = False
        if book_metadata['cover_image_data']:
            try:
                cover_image_base64 = base64.b64encode(book_metadata['cover_image_data']).decode('utf-8')
                has_cover = True
            except Exception as e:
                logger.warning(f"Failed to encode cover image: {str(e)}")
                cover_image_base64 = None
                has_cover = False
        book_meta = [{
            'identifier': book_metadata['identifier'],
            'title': book_metadata['title'],
            'authors': book_metadata['authors'],
            'series': book_metadata['series'],
            'seriesindex': book_metadata['seriesindex'],
            'relative_path': book_metadata['relative_path'],
            'coverImageData': cover_image_base64,
            'coverMediaType': book_metadata['cover_media_type'] if has_cover else None,
            'hasCover': has_cover
        }]
        return jsonify({
            'message': 'File uploaded successfully',
            'book_metadata': book_meta
        }), 200
    except Exception as e:
        if os.path.exists(file_filepath):
            os.remove(file_filepath)
        logger.error(f"Error during file upload: {str(e)}")
        return jsonify({'error': 'Internal server error during upload'}), 500


@books_bp.route('/api/books/upload/cancel/<path:path>', methods=['DELETE'])
def cancel_upload(path):
    logger.info(path)
    decoded_path = unquote(path)
    full_path = os.path.join(config.BASE_DIRECTORY, decoded_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        return jsonify ({
            'message': 'Upload cancelled successfully'
        }), 200
    else:
        return jsonify ({
            'error': 'Upload not found'
        }), 404


@books_bp.route('/api/books/add', methods=['POST'])
@login_required(required_roles=["admin", "editor"])
def add_book(token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    identifier = request.form.get('identifier')
    new_title = request.form.get('title')
    new_authors = request.form.get('authors')
    new_series = request.form.get('series')
    new_seriesindex = request.form.get('seriesindex')
    new_cover = request.files.get('coverImage')
    relative_path = request.form.get('relative_path')
    session = get_session()
    try:
        book_file = os.path.join(config.BASE_DIRECTORY, relative_path)
        metadata = get_metadata(book_file, config.BASE_DIRECTORY)
        if new_title:
            metadata['title'] = new_title
        if new_authors:
            metadata['authors'] = [author.strip() for author in new_authors.split(',')]
        if new_series:
            metadata['series'] = new_series
        if new_seriesindex is not None:
            try:
                metadata['seriesindex'] = float(new_seriesindex)
            except ValueError:
                return jsonify({"error": "Invalid series index format"}), 400
        if new_seriesindex is None:
            metadata['seriesindex'] = float(0.0)
        if new_cover:
            metadata['cover_image_data'] = new_cover.read()
            metadata['cover_media_type'] = new_cover.mimetype
        success = add_new_db_entry(session, identifier, metadata)
        if success:
            session.commit()
            return jsonify({'message': 'Book added successfully'}), 200
        else:
            return jsonify({'error': 'Failed to add book, duplicate entry'}), 409
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "An unexpected error occurred."}), 500
    finally:
        session.close()


@books_bp.route('/api/books/edit', methods=['POST'])
@login_required(required_roles=["admin", "editor"])
def edit_book_metadata(token_state):
    """
    Handles editing metadata for a book. Updates only the database.
    """
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    identifier = request.form.get('identifier')
    new_title = request.form.get('title')
    new_authors = request.form.get('authors')
    new_series = request.form.get('series')
    new_seriesindex = request.form.get('seriesindex')
    new_cover = request.files.get('coverImage')
    session = get_session()
    try:
        book_record = session.query(EpubMetadata).filter_by(identifier=identifier).first()
        if not book_record:
            return jsonify({"error": "Book not found"}), 404
        if config.WRITE_TO_EPUB:
            book_file = os.path.join(config.BASE_DIRECTORY, book_record.relative_path)
            book = ebookmeta.get_metadata(book_file)
            if new_title:
                book.title = new_title
            if new_authors:
                book.set_author_list_from_string(new_authors)
            if new_series:
                book.series = new_series
            if new_seriesindex is not None:
                try:
                    book.series_index = float(new_seriesindex)
                except ValueError:
                    return jsonify({"error": "Invalid series index format"}), 400
            if new_seriesindex is None:
                book.series_index = float(0.0)
            if new_cover:
                if not book.cover_image_data or len(book.cover_image_data) <= 10:
                    return jsonify({"error": "BookHaven can only replace existing cover images, but at this time can not add new ones."}), 400
                else:
                    book.cover_image_data = new_cover.read()
                    book.cover_media_type = new_cover.mimetype
            ebookmeta.set_metadata(book_file, book)
        if new_title:
            book_record.title = new_title
        if new_authors:
            book_record.authors = new_authors
        if new_series:
            book_record.series = new_series
        if new_seriesindex is not None:
            try:
                book_record.seriesindex = float(new_seriesindex)
            except ValueError:
                return jsonify({"error": "Invalid series index format"}), 400
        if new_seriesindex is None:
            book_record.seriesindex = float(0.0)
        if new_cover:
            book_record.cover_image_data = new_cover.read()
            book_record.cover_media_type = new_cover.mimetype
        session.commit()
        return jsonify({"message": "Book metadata updated successfully"}), 200
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "An unexpected error occurred."}), 500
    finally:
        session.close()


@books_bp.route('/api/books/<string:book_identifier>', methods=['GET'])
@login_required
def get_book_details_by_identifier(book_identifier, token_state):
    session = get_session()
    try:
        book_record = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
        if not book_record:
            return jsonify({"error": f"No book found with identifier {book_identifier}"}), 404
        if token_state != "no_token":
            book_progress_status, book_progress = get_book_progress(token_state, book_identifier, session)
            if not book_progress_status:
                book_progress_progress = None
            else:
                book_progress_progress = book_progress.progress
        else:
            book_progress_progress = None
        book_details = {
            "identifier": book_record.identifier,
            "epubUrl": config.BASE_URL.rstrip("/") + url_for("media.stream", book_identifier=book_record.identifier),
            "progress": book_progress_progress,
        }
        return jsonify(book_details), 200
    finally:
        session.close()


@books_bp.route('/api/books/<string:book_identifier>/progress_state', methods=['PUT'])
@login_required
def update_progress_state(book_identifier, token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Missing request data"}), 400
    if not any(key in data for key in ['is_finished', 'progress', 'favorite']):
        return jsonify(
            {"error": "Missing one of these keys in request data: 'is_finished', 'progress', 'favorite'"}), 400

    session = get_session()
    try:
        book_record = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
        if not book_record:
            return jsonify({"error": "Book not found"}), 404

        update_status, message = update_book_progress_state(token_state, book_identifier, data)
        if not update_status:
            return jsonify({"error": message}), 404
        return jsonify({"message": "Book progress updated successfully"}), 200
    finally:
        session.close()


@books_bp.route('/api/books/requests', methods=['POST'])
@login_required
def new_request(token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Missing request data"}), 400
    if not any(key in data for key in ['title', 'authors']):
        return jsonify({"error": "Missing title or author"}), 400
    session = get_session()
    try:
        new_entry = Requests(
            request_user_id=token_state.get("user_id"),
            request_title=data.get('title'),
            request_authors=data.get('authors'),
            request_series=data.get('series', ''),
            request_seriesindex=float(data.get('seriesindex', 0.0)),
            request_link=data.get('link', ''),
        )
        session.add(new_entry)
        session.commit()
        return jsonify({"message": "Request submitted successfully"}), 200
    except IntegrityError:
        logger.warning(f"Duplicate entry")
        session.rollback()
        return jsonify({"error": "This request has already been submitted"}), 409
    except Exception as e:
        logger.error(f"Error creating book request: {e}")
        session.rollback()
        return jsonify({"error": "An error occurred while processing your request"}), 500
    finally:
        session.close()


@books_bp.route('/api/books/requests', methods=['GET'])
@login_required
def get_requests(token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401

    offset = request.args.get('offset', 0, type=int)
    limit = min(request.args.get('limit', 20, type=int), 20)  # Max 20 per page
    sort_by = request.args.get('sort_by', 'date', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)

    session = get_session()
    try:
        # Get current user's role
        current_user = session.query(Users).filter(Users.id == token_state['user_id']).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Join with Users table to get username
        requests_query = session.query(Requests, Users.username).join(
            Users, Requests.request_user_id == Users.id
        )

        # Filter based on user role
        if current_user.role not in ['admin', 'editor']:
            requests_query = requests_query.filter(Requests.request_user_id == token_state['user_id'])

        # Configure sorting
        if sort_by == 'title':
            order_field = Requests.request_title
        elif sort_by == 'authors':
            order_field = Requests.request_authors
        elif sort_by == 'series':
            order_field = Requests.request_series
        elif sort_by == 'user':
            order_field = Users.username
        else:  # Default to 'date'
            order_field = Requests.request_date

        if sort_order == 'asc':
            requests_query = requests_query.order_by(order_field.asc())
        else:  # Default to 'desc'
            requests_query = requests_query.order_by(order_field.desc())

        total_requests = requests_query.count()
        requests_list = requests_query.offset(offset).limit(limit).all()

        request_data = []
        for req, username in requests_list:
            request_data.append({
                "id": req.id,
                "user_id": req.request_user_id,
                "username": username,
                "date": req.request_date.isoformat() if req.request_date else None,
                "title": req.request_title,
                "authors": req.request_authors,
                "series": req.request_series,
                "seriesindex": req.request_seriesindex,
                "link": req.request_link
            })

        return jsonify({
            "requests": request_data,
            "total_requests": total_requests,
            "fetched_offset": offset,
            "next_offset": offset + limit,
            "remaining_requests": max(0, total_requests - (offset + limit))
        })

    except Exception as e:
        logger.error(f"Error fetching book requests: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()


@books_bp.route('/api/books/requests/<int:request_id>', methods=['DELETE'])
@login_required
def delete_request(token_state, request_id):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401

    session = get_session()
    try:
        # Get current user's role
        current_user = session.query(Users).filter(Users.id == token_state['user_id']).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Find the request to delete
        request_to_delete = session.query(Requests).filter(Requests.id == request_id).first()
        if not request_to_delete:
            return jsonify({"error": "Request not found"}), 404

        # Check permissions
        if current_user.role not in ['admin', 'editor']:
            # Regular users can only delete their own requests
            if request_to_delete.request_user_id != token_state['user_id']:
                return jsonify({"error": "You can only delete your own requests"}), 403

        # Delete the request
        session.delete(request_to_delete)
        session.commit()

        return jsonify({"message": "Request deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting book request: {e}")
        session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()
