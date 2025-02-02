from sqlalchemy import or_, and_
from flask import Blueprint, request, jsonify, url_for
from models.epub_metadata import EpubMetadata
from models.progress_mapping import ProgressMapping
from functions.db import get_session
from functions.book_management import get_book_progress, update_book_progress_state, login_required
from config.config import config, str_to_bool
from config.logger import logger
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


@books_bp.route('/api/books/edit', methods=['POST'])
@login_required
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
    if not data:
        return jsonify({"error": "Missing request data"}), 400
    if not any(key in data for key in ['is_finished', 'progress', 'favorite']):
        return jsonify({"error":"Missing one of these keys in request data: 'is_finished', ', 'progress', 'favorite'"}), 400
    session = get_session()
    try:
        book_record = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
        if not book_record:
            return jsonify({"error": "Book not found"}), 404
    finally:
        session.close()
    update_status, message = update_book_progress_state(token_state, book_identifier, data)
    if not update_status:
        return jsonify({"error": message}), 404
    return jsonify({"message": "Book progress updated successfully"}), 200