from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.epub_metadata import Base
from config.config import config

# Dynamically construct the database URL
DATABASE_URL = config.get_database_url()

engine = create_engine(DATABASE_URL)


def init_db():
    """
    Initializes the database by creating necessary tables.
    """
    Base.metadata.create_all(engine)


def get_session():
    """
    Provides a new database session (connection).
    """
    Session = sessionmaker(bind=engine)
    return Session()