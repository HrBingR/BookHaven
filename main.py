import os
from ebooklib import epub
from flask import Flask, render_template, send_from_directory
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


app = Flask(__name__)

def find_epubs(base_directory):
    epubs = []
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith(".epub"):
                full_path = os.path.join(root, file)
                epubs.append(full_path)
    return epubs

def extract_metadata(epub_path, base_directory):
    book = epub.read_epub(epub_path)
    title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'Unknown'
    authors = [creator[0] for creator in book.get_metadata('DC', 'creator')]
    relative_path = os.path.relpath(epub_path, base_directory)
    print(relative_path)
    return {'title': title, 'authors': authors, 'relative_path': relative_path}

@app.route('/')
def index():
    base_directory = '/home/anthony/epubs'
    epubs = find_epubs(base_directory)
    metadata = [extract_metadata(epub, base_directory) for epub in epubs]
    return render_template('index.html', books=metadata)

@app.route('/download/<path:relative_path>')
def download(relative_path):
    base_directory = '/home/anthony/epubs'
    return send_from_directory(base_directory, relative_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)