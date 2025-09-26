from sqlalchemy import Column, Integer, String, Float, Index
from models.base import Base

class EpubMetadata(Base):
    __tablename__ = 'epub_metadata'

    id = Column(Integer, primary_key=True)
    identifier = Column(String(255), unique=True, nullable=False) # Add 'index=True'
    title = Column(String(255))
    authors = Column(String(255))
    series = Column(String(255))
    seriesindex = Column(Float)
    relative_path = Column(String(255), unique=True)
    cover_image_path = Column(String(255), nullable=True)
    progress = Column(String(255), nullable=True)

    __table_args__ = (
        Index('book_identifier', 'identifier', unique=True),
        Index('author_title_index_series_idx', 'authors', 'series', 'seriesindex', 'title', unique=True)
    )
