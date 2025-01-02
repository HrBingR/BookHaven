import os
import threading
from flask import Flask, render_template, abort, send_from_directory, request, jsonify, Response, has_request_context
from models.epub_metadata import EpubMetadata
from functions.db import init_db, get_session
from functions.metadata.scan import scan_and_store_metadata
from config.config import config
from config.logger import logger
from urllib.parse import quote

# from functions.metadata.edit import edit_metadata
scan_lock = threading.Lock()

app = Flask(__name__)
init_db()
library_initialized = False

@app.before_request
def initialize_library_once():
    """
       This function checks if the library is initialized.
       If it is not, it triggers a library scan the first time a request happens.
       """
    global library_initialized
    global scan_lock

    if not library_initialized and has_request_context():
        session = get_session()
        total_books = session.query(EpubMetadata).count()

        if total_books == 0:
            with scan_lock:  # Ensure only one scan runs at a time
                if not library_initialized:  # Double-check inside the lock
                    logger.info("No books found in database on app startup. Triggering library scan.")
                    base_directory = config.BASE_DIRECTORY
                    scan_and_store_metadata(base_directory)
                    logger.info("Library scan complete and database populated.")
                    library_initialized = True
        else:
            library_initialized = True
            logger.info("Books already exist in database. No scan required.")


def format_series_index(value):
    if value.is_integer():
        return str(int(value))
    return str(value)

app.jinja_env.filters['format_series_index'] = format_series_index

@app.route('/api/books', methods=['GET'])
def get_books():
    """
    Returns a JSON response of books with optional search and pagination.
    """
    # Get query and pagination parameters
    query = request.args.get('query', '', type=str)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit

    session = get_session()

    # Base query
    books_query = session.query(EpubMetadata)

    # Apply search filter (title, authors, series)
    if query:
        query_like = f"%{query}%"
        books_query = books_query.filter(
            (EpubMetadata.title.ilike(query_like)) |
            (EpubMetadata.authors.ilike(query_like)) |
            (EpubMetadata.series.ilike(query_like))
        )

    # Pagination
    total_books = books_query.count()
    books = books_query.offset(offset).limit(limit).all()

    # Convert book metadata to JSON
    book_list = []
    for book in books:
        # Add debug logging to see the full relative_path
        logger.debug(f"Constructing cover URL for book id={book.id}, relative_path={book.relative_path}")

        book_list.append({
            "id": book.id,
            "title": book.title,
            "authors": book.authors.split(", "),
            "series": book.series,
            "seriesindex": book.seriesindex,
            "coverUrl": f"/api/covers/{quote(book.relative_path)}",
            "relative_path": book.relative_path,
        })

    return jsonify({
        "books": book_list,
        "total_books": total_books,
        "current_page": page,
        "total_pages": (total_books + limit - 1) // limit  # Ceiling division
    })

@app.route('/api/covers/<path:relative_path>', methods=['GET'])
def get_cover(relative_path):
    """
    Returns the cover of the ePub file from the database. Serves a placeholder if not available.
    """
    session = get_session()

    # Retrieve the book record from the database
    book_record = session.query(EpubMetadata).filter_by(relative_path=relative_path).first()

    if not book_record or not book_record.cover_image_data:
        # If no record or no cover image, serve a placeholder
        placeholder_path = os.path.join(app.static_folder, 'placeholder.jpg')
        with open(placeholder_path, 'rb') as f:
            placeholder_image = f.read()
        return Response(placeholder_image, mimetype='image/jpeg')

    # Serve the cover image data from the database
    return Response(book_record.cover_image_data, mimetype=book_record.cover_media_type)

@app.route('/api/scan', methods=['POST'])
def scan_library():
    """
       Trigger a manual scan of the library.
       Prevent concurrent scans using a threading lock.
       """
    global scan_lock

    with scan_lock:
        logger.info("Manual scan triggered.")
        base_directory = config.BASE_DIRECTORY
        scan_and_store_metadata(base_directory)
        logger.info("Manual scan complete.")
        return jsonify({"message": "Library scanned successfully"}), 200

@app.route('/')
def index():
    session = get_session()
    books = session.query(EpubMetadata).all()
    return render_template('index.html', books=books)


@app.route('/download/<path:relative_path>', methods=['GET'])
def download(relative_path):
    session = get_session()

    # Optionally validate that the relative_path exists in the database
    book_record = session.query(EpubMetadata).filter_by(relative_path=relative_path).first()
    if not book_record:
        abort(404, description="Resource not found")

    # Ensure the base directory remains consistent
    try:
        return send_from_directory(config.BASE_DIRECTORY, relative_path, as_attachment=True)
    except FileNotFoundError:
        abort(404, description="File not found")

if __name__ == '__main__':
    app.run(debug=True)