from functions.db import get_session
from models.epub_metadata import EpubMetadata

def edit_metadata(relative_path, new_title=None, new_authors=None):
    session = get_session()
    book_record = session.query(EpubMetadata).filter_by(relative_path=relative_path).first()

    if book_record:
        if new_title:
            book_record.title = new_title
        if new_authors:
            book_record.authors = ', '.join(new_authors)

        session.commit()