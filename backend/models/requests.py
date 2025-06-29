from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Index, Float
from models.base import Base

class Requests(Base):
    __tablename__ = 'requests'
    __table_args__ = (
        Index('ix_requests_id', 'id'),
        Index('ix_requests_title_authors', 'request_title', 'request_authors', unique=True),
        Index('ix_requests_date', 'request_date')
    )

    id = Column(Integer, primary_key=True)
    request_user_id = Column(Integer, nullable=False)
    request_date = Column(DateTime, default=datetime.now(timezone.utc))
    request_title = Column(String(255), nullable=False)
    request_authors = Column(String(255), nullable=False)
    request_series = Column(String(255))
    request_seriesindex = Column(Float)
    request_link = Column(String(255))
