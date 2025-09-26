import os
from flask import Blueprint, Response, current_app as app, send_from_directory, jsonify, abort, url_for, request
from models.epub_metadata import EpubMetadata
from functions.db import get_session
from functions.roles import login_required
from functions.utils import update_redis_cache, invalidate_redis_cache
from config.config import config

media_bp = Blueprint('media', __name__)


def get_redis_cache(identifier, cache_name):
    if cache_name not in ('image_path_cache', 'book_path_cache'):
        return None
    if not identifier:
        return None
    redis_client = getattr(app, "redis", None)
    if not redis_client:
        return None
    return redis_client.hget(cache_name, identifier)


@media_bp.route('/api/covers/<string:book_identifier>', methods=['GET'])
def get_cover(book_identifier):
    """
    Serve cover images with browser-side caching enabled to reduce repeated requests.
    """
    def _return_placeholder():
        placeholder_path = os.path.join(app.static_folder, 'placeholder.jpg')
        with open(placeholder_path, 'rb') as f:
            placeholder_image = f.read()
        return Response(placeholder_image, mimetype='image/jpeg', headers={
            "Cache-Control": "public, max-age=259200"
        })
    def _get_image_from_path(path):
        cover_image_path = os.path.join(config.COVER_BASE_DIRECTORY, path)
        if not os.path.isfile(cover_image_path):
            invalidate_redis_cache(book_identifier)
            return _return_placeholder()
        with open(cover_image_path, 'rb') as f:
            cover_image = f.read()
            return Response(cover_image, mimetype="image/webp", headers={
                "Cache-Control": "public, max-age=259200"
            })
    cover_image_path = get_redis_cache(book_identifier, "image_path_cache")
    if cover_image_path:
        return _get_image_from_path(cover_image_path)
    session = get_session()
    try:
        book_record = session.query(EpubMetadata).filter_by(identifier=str(book_identifier)).first()
        if not book_record or not book_record.cover_image_path:
            return _return_placeholder()
        meta = {'identifier': book_identifier, 'cover_image_path': book_record.cover_image_path,
                'relative_path': book_record.relative_path}
        update_redis_cache(meta)
        return _get_image_from_path(book_record.cover_image_path)
    finally:
        session.close()


@media_bp.route('/download/<string:book_identifier>', methods=['GET'])
@login_required
def download(book_identifier):
    relative_path = get_redis_cache(book_identifier, "book_path_cache")
    if not relative_path:
        session = get_session()
        book_record = session.query(EpubMetadata).filter_by(identifier=str(book_identifier)).first()
        if not book_record:
            abort(404, description="Resource not found")
        relative_path = book_record.relative_path
        meta = {'identifier': book_identifier, 'cover_image_path': book_record.cover_image_path,
                'relative_path': book_record.relative_path}
        update_redis_cache(meta)
    try:
        custom_file_header = request.headers.get("file")
        if config.ENVIRONMENT == "test" and custom_file_header == "not_found":
            raise FileNotFoundError
        return send_from_directory(config.BASE_DIRECTORY, relative_path, as_attachment=True)
    except FileNotFoundError:
        invalidate_redis_cache(book_identifier)
        abort(404, description="File not found")


@media_bp.route('/stream/<string:book_identifier>', methods=['GET'])
def stream(book_identifier):
    relative_path = get_redis_cache(book_identifier, "book_path_cache")
    if not relative_path:
        session = get_session()
        book_record = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
        if not book_record:
            abort(404, description="Book not found.")
        relative_path = book_record.relative_path
        meta = {'identifier': book_identifier, 'cover_image_path': book_record.cover_image_path,
                'relative_path': book_record.relative_path}
        update_redis_cache(meta)
    full_path = os.path.join(config.BASE_DIRECTORY, relative_path)
    if not os.path.exists(full_path):
        invalidate_redis_cache(book_identifier)
        abort(404, description="ePub file not found.")
    epub_file_url = config.BASE_URL.rstrip("/") + url_for('media.serve_book_file', filename=relative_path)
    return jsonify({"url": epub_file_url})


@media_bp.route('/files/<path:filename>', methods=['GET'])
def serve_book_file(filename):
    try:
        base_directory = config.BASE_DIRECTORY  # Root location of your ePub files
        custom_file_header = request.headers.get("file")
        if config.ENVIRONMENT == "test" and custom_file_header == "not_found":
            raise FileNotFoundError
        return send_from_directory(base_directory, filename)
    except FileNotFoundError:
        abort(404, description="File not found.")
