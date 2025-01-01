from flask import Flask, render_template, abort, send_from_directory
from models.epub_metadata import EpubMetadata
from functions.db import init_db, get_session
from functions.metadata.scan import scan_and_store_metadata
from config.config import config
from functions.metadata.edit import edit_metadata

app = Flask(__name__)

init_db()

def format_series_index(value):
    if value.is_integer():
        return str(int(value))
    return str(value)

app.jinja_env.filters['format_series_index'] = format_series_index

@app.route('/')
def index():
    base_directory = config.BASE_DIRECTORY
    scan_and_store_metadata(base_directory)
    session = get_session()
    books = session.query(EpubMetadata).all()
    return render_template('index.html', books=books)


@app.route('/download/<path:relative_path>')
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