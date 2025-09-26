"""Migrate from DB image storage start

Revision ID: 462141604020
Revises: 9dd6804d59a2
Create Date: 2025-09-24 22:44:37.836362

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '462141604020'
down_revision: Union[str, None] = '9dd6804d59a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('epub_metadata', sa.Column('cover_image_path', sa.String(length=255), nullable=True))
    op.drop_column('epub_metadata', 'cover_media_type')


def downgrade() -> None:
    op.drop_column('epub_metadata', 'cover_image_path')
    op.add_column('epub_metadata', sa.Column('cover_media_type', sa.String(length=255), nullable=True))
