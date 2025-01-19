from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from models.base import Base

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    oidc_user_id = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login = Column(DateTime, default=datetime.now(timezone.utc))
    failed_login_count = Column(Integer, default=0, nullable=False)
    auth_type = Column(Enum('oidc', 'local'), default='local', nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    last_used_otp = Column(Integer, nullable=True)