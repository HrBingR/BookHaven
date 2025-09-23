from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from models.base import Base

class ProgressMapping(Base):
    __tablename__ = 'progress_mapping'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    book_id = Column(Integer, nullable=False)
    progress = Column(String(255), nullable=True)
    is_finished = Column(Boolean, default=False, nullable=False)
    marked_favorite = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_user_book', 'user_id', 'book_id', unique=True),  # unique=True if you want to ensure uniqueness
    )
