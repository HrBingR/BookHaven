from flask import Blueprint, jsonify
from models.epub_metadata import EpubMetadata
from functions.db import get_session
from functions.book_management import login_required

authors_bp = Blueprint('authors', __name__)

@authors_bp.route('/api/authors', methods=['GET'])
@login_required
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

@authors_bp.route('/api/authors/<string:author_name>', methods=['GET'])
@login_required
def get_author_books(author_name):
    """
    Returns all books by a specific author.
    """
    session = get_session()

    normalized_author_name = author_name.replace('-', ' ').lower()

    # Query books with case-insensitive match
    author_query = session.query(EpubMetadata).filter(
        EpubMetadata.authors.ilike(f"%{normalized_author_name}%")
    ).all()

    if not author_query:
        # Return a 404 if no books are found for the author
        return jsonify({"error": f"No books found for author: {author_name}"}), 404

    # Format results into a JSON response
    books = [{
        "id": book.id,
        "title": book.title,
        "authors": book.authors.split(", "),
        "series": book.series,
        "seriesindex": book.seriesindex,
        "coverUrl": f"/api/covers/{book.identifier}",
        "relative_path": book.relative_path,
        "identifier": book.identifier,
    } for book in author_query]

    return jsonify({
        "author": author_name,
        "books": books,
        "total_books": len(books)
    }), 200