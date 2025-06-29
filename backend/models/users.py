from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, Index
from models.base import Base
from typing import Optional

auth_type_enum = Enum('oidc', 'local', name='auth_type')
roles_enum = Enum('admin', 'editor', 'user', name='roles')

class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_id', 'id'),
        Index('ix_users_email', 'email'),
        Index('ix_users_oidc_user_id', 'oidc_user_id'),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    role = Column(roles_enum, default='user', nullable=False)
    oidc_user_id: Optional[str] = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login = Column(DateTime, default=datetime.now(timezone.utc))
    failed_login_count = Column(Integer, default=0, nullable=False)
    auth_type = Column(auth_type_enum, default='local', nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    last_used_otp = Column(String(8), nullable=True)