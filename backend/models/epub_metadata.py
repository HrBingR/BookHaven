from sqlalchemy import Column, Integer, String, Float, LargeBinary, Index
from sqlalchemy.dialects.mysql import LONGBLOB
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
    cover_image_data = Column(LargeBinary().with_variant(LONGBLOB, 'mysql'))
    cover_media_type = Column(String(255))
    progress = Column(String(255), nullable=True)

    __table_args__ = (
        Index('book_identifier', 'identifier', unique=True),
        Index('author_title_index_series_idx', 'authors', 'series', 'seriesindex', 'title', unique=True)
    )