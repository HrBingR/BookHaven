from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class EpubMetadata(Base):
    __tablename__ = 'epub_metadata'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    authors = Column(String)
    series = Column(String)
    seriesindex = Column(Float)
    relative_path = Column(String, unique=True)