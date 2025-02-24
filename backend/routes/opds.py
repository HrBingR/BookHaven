import binascii
import base64
import uuid
from flask import Blueprint, request, make_response, current_app, Response
from typing import cast
from functions.db import get_session
from functions.init import CustomFlask
from bcrypt import checkpw
from models.users import Users
from datetime import datetime, timezone
from config.logger import logger
from xml.etree import ElementTree
from models.epub_metadata import EpubMetadata
from urllib.parse import urljoin, quote
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

def basic_auth():
    app = cast(CustomFlask, current_app)
    redis = app.redis
    if not redis:
        logger.debug("Failed to access redis client")
        response = make_response('', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
        return response
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Basic '):
        logger.debug("Missing auth header")
        response = make_response('', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
        return response

    try:
        token = auth.split(' ')[1]
        decoded_credentials = base64.b64decode(token).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
    except (IndexError, ValueError, binascii.Error):
        logger.debug("Invalid basic auth format")
        response = make_response('', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
        return response

    # Check Redis for an existing session
    session_data = redis.get(f"user_session:{username}")
    if session_data:
        try:
            user_id = int(session_data)
            session = get_session()
            try:
                user = session.query(Users).filter(Users.id == user_id).first()
                if user:
                    return user
            finally:
                session.close()
        except ValueError:
            # Invalid session data in Redis
            redis.delete(f"user_session:{username}")

    # If no session found in Redis, validate credentials against database
    session = get_session()
    try:
        user = session.query(Users).filter((Users.username == username) | (Users.email == username)).first()

        # Use constant-time comparison for password check
        if not user or not checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            logger.error("User auth failed")
            response = make_response('', 401)
            response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
            return response

        # Create and store session in Redis with both username and session token
        session_token = str(uuid.uuid4())
        redis_key = f"user_session:{username}:{session_token}"
        redis.set(redis_key, user.id, ex=app.config.get('SESSION_LIFETIME', 86400))

        # Update last_login timestamp
        user.last_login = datetime.now(timezone.utc)
        session.commit()

        return user

    except SQLAlchemyError as e:
        logger.error(f"Database error during Basic Auth: {str(e)}")
        response = make_response('', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
        return response
    except RedisError as e:
        logger.error(f"Redis error during Basic Auth: {str(e)}")
        response = make_response('', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
        return response
    except Exception as e:
        logger.error(f"Unexpected error during Basic Auth: {str(e)}")
        response = make_response('', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="OPDS Catalog"'
        return response
    finally:
        session.close()

opds_bp = Blueprint('opds', __name__)
@opds_bp.route('/opds', methods=['GET'])
def opds_root():
    """
    Root OPDS feed that provides navigation to other feeds
    """
    user = basic_auth()
    if not isinstance(user, Users):
        return user  # Return error response if authentication failed

    # Create the root element with necessary namespaces
    feed = ElementTree.Element('feed', {
        'xmlns': 'https://www.w3.org/2005/Atom',
        'xmlns:dcterms': 'https://purl.org/dc/terms/',
        'xmlns:opds': 'https://opds-spec.org/2010/catalog'
    })

    # Add required feed elements
    ElementTree.SubElement(feed, 'id').text = request.url_root + 'opds'
    ElementTree.SubElement(feed, 'title').text = 'BookHaven OPDS Catalog'
    ElementTree.SubElement(feed, 'updated').text = datetime.now(timezone.utc).isoformat() + 'Z'

    author = ElementTree.SubElement(feed, 'author')
    ElementTree.SubElement(author, 'name').text = 'Library Server'

    # Add navigation links
    add_link(feed, 'self', request.url, 'application/atom+xml;profile=opds-catalog;kind=navigation')
    add_link(feed, 'start', urljoin(request.url_root, 'opds'),
             'application/atom+xml;profile=opds-catalog;kind=navigation')

    # Add entry for all books catalog
    books_entry = ElementTree.SubElement(feed, 'entry')
    add_root_entry(books_entry, 'All Books', 'opds/all')

    authors_entry = ElementTree.SubElement(feed, 'entry')
    add_root_entry(authors_entry, 'Authors', 'opds/authors')

    # Convert to string and return as XML response
    return Response(ElementTree.tostring(feed, encoding='unicode'),
                    mimetype='application/atom+xml')

@opds_bp.route('/opds/all', methods=['GET'])
def opds_all_books():
    """
    OPDS feed that lists all available books
    """
    user = basic_auth()
    if not isinstance(user, Users):
        return user
    session = get_session()
    try:
        # Query books with pagination
        books_query = session.query(EpubMetadata).order_by(
            EpubMetadata.authors,
            EpubMetadata.series,
            EpubMetadata.seriesindex,
            EpubMetadata.title
        )
        books, feed = setup_feed(books_query, 'All Books', 'opds/all')
        for book in books:
            add_book_entries(feed, book)
        return Response(ElementTree.tostring(feed, encoding='unicode'),
                        mimetype='application/atom+xml')
    finally:
        session.close()

@opds_bp.route('/opds/authors', methods=['GET'])
def opds_get_authors():
    user = basic_auth()
    if not isinstance(user, Users):
        return user
    session = get_session()
    try:
        authors_query = session.query(EpubMetadata.authors).distinct().order_by(
            EpubMetadata.authors
        )
        authors, feed = setup_feed(authors_query, 'Authors', 'opds/authors')
        for author in authors:
            entry = ElementTree.SubElement(feed, 'entry')
            ElementTree.SubElement(entry, 'title').text = author[0]
            author_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"author:{author[0]}")
            ElementTree.SubElement(entry, 'id').text = f'urn:uuid:{author_uuid}'
            ElementTree.SubElement(entry, 'updated').text = datetime.now(timezone.utc).isoformat() + 'Z'
            add_link(entry, 'subsection', urljoin(request.url_root, f'opds/authors/{quote(author[0])}'),
                     'application/atom+xml;profile=opds-catalog;kind=acquisition')
        return Response(ElementTree.tostring(feed, encoding='unicode'),
                        mimetype='application/atom+xml')
    finally:
        session.close()

@opds_bp.route('/opds/authors/<string:author_name>', methods=['GET'])
def opds_get_author_name(author_name):
    user = basic_auth()
    if not isinstance(user, Users):
        return user
    session = get_session()
    try:
        normalized_author_name = author_name.replace('-', ' ').lower()
        books_query = session.query(EpubMetadata).filter(
            EpubMetadata.authors.ilike(f"%{normalized_author_name}%")
        )
        books, feed = setup_feed(books_query, author_name, f'opds/authors/{author_name}')
        for book in books:
            add_book_entries(feed, book)
        return Response(ElementTree.tostring(feed, encoding='unicode'),
                        mimetype='application/atom+xml')
    finally:
        session.close()

def add_root_entry(entry, title, link):
    ElementTree.SubElement(entry, 'title').text = title
    ElementTree.SubElement(entry, 'id').text = urljoin(request.url_root, link)
    ElementTree.SubElement(entry, 'updated').text = datetime.now(timezone.utc).isoformat() + 'Z'
    add_link(entry, 'subsection', urljoin(request.url_root, link),
             'application/atom+xml;profile=opds-catalog;kind=acquisition')

def setup_feed(query, title, link):
    page = request.args.get('page', 1, type=int)
    per_page = 30
    query_count = query.count()
    query_items = query.offset((page - 1) * per_page).limit(per_page).all()
    feed = ElementTree.Element('feed', {
        'xmlns': 'https://www.w3.org/2005/Atom',
        'xmlns:dcterms': 'https://purl.org/dc/terms/',
        'xmlns:opds': 'https://opds-spec.org/2010/catalog'
    })
    ElementTree.SubElement(feed, 'id').text = request.url
    ElementTree.SubElement(feed, 'title').text = title
    ElementTree.SubElement(feed, 'updated').text = datetime.now(timezone.utc).isoformat() + 'Z'

    add_link(feed, 'self', request.url, 'application/atom+xml;profile=opds-catalog;kind=acquisition')
    add_link(feed, 'start', urljoin(request.url_root, link),
             'application/atom+xml;profile=opds-catalog;kind=navigation')
    if page > 1:
        prev_url = urljoin(request.url_root, f'{link}?page={page - 1}')
        add_link(feed, 'previous', prev_url, 'application/atom+xml;profile=opds-catalog;kind=acquisition')

    if (page * per_page) < query_count:
        next_url = urljoin(request.url_root, f'{link}?page={page + 1}')
        add_link(feed, 'next', next_url, 'application/atom+xml;profile=opds-catalog;kind=acquisition')
    return query_items, feed

def add_link(parent, rel, href, type_):
    """Helper function to add link elements"""
    ElementTree.SubElement(parent, 'link', {
        'rel': rel,
        'href': href,
        'type': type_
    })

def add_book_entries(feed, book):
    entry = ElementTree.SubElement(feed, 'entry')

    ElementTree.SubElement(entry, 'title').text = book.title
    ElementTree.SubElement(entry, 'id').text = f'urn:uuid:{book.identifier}'
    ElementTree.SubElement(entry, 'updated').text = datetime.now(timezone.utc).isoformat() + 'Z'

    # Add author information
    for author_name in book.authors.split(", "):
        author = ElementTree.SubElement(entry, 'author')
        ElementTree.SubElement(author, 'name').text = author_name

    # Add links for cover image and download
    cover_url = urljoin(request.url_root, f'api/covers/{book.identifier}')
    add_link(entry, 'http://opds-spec.org/image', cover_url, book.cover_media_type)

    thumbnail_url = urljoin(request.url_root, f'api/covers/{book.identifier}')
    add_link(entry, 'http://opds-spec.org/image/thumbnail', thumbnail_url, book.cover_media_type)

    # Add download link
    download_url = urljoin(request.url_root, f'download/{book.identifier}')
    add_link(entry, 'http://opds-spec.org/acquisition', download_url, 'application/epub+zip')

    # Add series information if available
    if book.series:
        series = ElementTree.SubElement(entry, 'dcterms:series')
        series.text = book.series
        if book.seriesindex:
            series_index = ElementTree.SubElement(entry, 'opds:seriesIndex')
            series_index.text = str(book.seriesindex)