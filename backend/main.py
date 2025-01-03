import os
import threading
from flask import Flask, render_template, abort, send_from_directory, request, jsonify, Response, has_request_context
from models.epub_metadata import EpubMetadata
from functions.db import init_db, get_session
from functions.metadata.scan import scan_and_store_metadata
from config.config import config
from config.logger import logger
from flask_caching import Cache

app = Flask(__name__)

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",  # Use in-memory caching for simplicity
    "CACHE_DEFAULT_TIMEOUT": 300  # Cache timeout in seconds (5 minutes)
})

# from functions.metadata.edit import edit_metadata
scan_lock = threading.Lock()

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
                    cache.clear()
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
@cache.cached(query_string=True)
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
            "coverUrl": f"/api/covers/{book.identifier}",
            "relative_path": book.relative_path,
            "identifier": book.identifier,
        })

    return jsonify({
        "books": book_list,
        "total_books": total_books,
        "current_page": page,
        "total_pages": (total_books + limit - 1) // limit  # Ceiling division
    })

@app.route('/api/covers/<string:book_identifier>', methods=['GET'])
def get_cover(book_identifier):
    """
    Serve cover images with browser-side caching enabled to reduce repeated requests.
    """
    session = get_session()
    book_record = session.query(EpubMetadata).filter_by(identifier=str(book_identifier)).first()

    if not book_record or not book_record.cover_image_data:
        placeholder_path = os.path.join(app.static_folder, 'placeholder.jpg')
        with open(placeholder_path, 'rb') as f:
            placeholder_image = f.read()
        # Set browser caching headers
        return Response(placeholder_image, mimetype='image/jpeg', headers={
            "Cache-Control": "public, max-age=31536000"  # Cache for 1 year
        })

    # Set browser caching headers for actual cover
    return Response(book_record.cover_image_data, mimetype=book_record.cover_media_type, headers={
        "Cache-Control": "public, max-age=31536000"  # Cache for 1 year
    })

@app.route('/api/scan', methods=['POST'])
def scan_library():
    """
       Trigger a manual scan of the library.
       Prevent concurrent scans using a threading lock.
       """
    global scan_lock

    with scan_lock:
        cache.clear()
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


@app.route('/download/<string:book_identifier>', methods=['GET'])
def download(book_identifier):
    session = get_session()

    # Optionally validate that the relative_path exists in the database
    book_record = session.query(EpubMetadata).filter_by(identifier=str(book_identifier)).first()
    if not book_record:
        abort(404, description="Resource not found")

    relative_path = book_record.relative_path

    # Ensure the base directory remains consistent
    try:
        return send_from_directory(config.BASE_DIRECTORY, relative_path, as_attachment=True)
    except FileNotFoundError:
        abort(404, description="File not found")

@app.route('/api/books/edit', methods=['POST'])
def edit_book_metadata():
    """
    Handles editing metadata for a book. Updates only the database.
    """
    session = get_session()
    identifier = request.form.get('identifier')
    new_title = request.form.get('title')
    new_authors = request.form.get('authors')  # Comma-separated string of authors
    new_series = request.form.get('series')
    new_seriesindex = request.form.get('seriesindex')
    new_cover = request.files.get('coverImage')  # For image uploads

    # Fetch the book record
    book_record = session.query(EpubMetadata).filter_by(identifier=identifier).first()
    if not book_record:
        return jsonify({"error": "Book not found"}), 404

    # Update metadata fields if provided
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
        try:
            book_record.seriesindex = float(0.0)
        except ValueError:
            return jsonify({"error": "Invalid series index format"}), 400

    # Update cover image and media type if uploaded
    if new_cover:
        book_record.cover_image_data = new_cover.read()
        book_record.cover_media_type = new_cover.mimetype

    session.commit()
    return jsonify({"message": "Book metadata updated successfully"}), 200

@app.route('/api/authors', methods=['GET'])
@cache.cached()
def get_authors():
    """
    Returns a list of distinct authors sorted alphabetically.
    """
    session = get_session()

    total_books = session.query(EpubMetadata.id).count()
    if total_books == 0:
        # Return an empty list if no books are found
        return jsonify({
            "authors": [],
            "total_authors": 0
        })

    authors_query = session.query(EpubMetadata.authors).all()

    # Flatten, deduplicate, and sort the authors
    authors = set()
    for entry in authors_query:
        if entry.authors:  # Only process non-empty author fields
            authors.update([author.strip() for author in entry.authors.split(",")])

    sorted_authors = sorted(authors)

    # Return the authors as JSON
    return jsonify({
        "authors": sorted_authors,
        "total_authors": len(sorted_authors)
    })

if __name__ == '__main__':
    app.run(debug=True)