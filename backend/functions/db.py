from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.epub_metadata import Base

DATABASE_URL = 'sqlite:///epub_library.db'
engine = create_engine(DATABASE_URL)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    Session = sessionmaker(bind=engine)
    return Session()