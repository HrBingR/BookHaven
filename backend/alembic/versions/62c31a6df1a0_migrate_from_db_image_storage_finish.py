"""Migrate from DB image storage finish

Revision ID: 62c31a6df1a0
Revises: 462141604020
Create Date: 2025-09-24 22:44:49.933762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '62c31a6df1a0'
down_revision: Union[str, None] = '462141604020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    needs_backfill = bind.execute(sa.text(
        """
        SELECT EXISTS (SELECT 1
                     FROM epub_metadata
                     WHERE cover_image_path IS NULL
                       AND cover_image_data IS NOT NULL
          LIMIT 1)
        """
    )).scalar_one()
    if needs_backfill:
        raise RuntimeError("BACKFILL_COVER_IMAGES_REQUIRED")
    op.drop_column('epub_metadata', 'cover_image_data')


def downgrade() -> None:
    op.add_column('epub_metadata', sa.Column('cover_image_data', sa.LargeBinary().with_variant(mysql.LONGBLOB(), 'mysql'), nullable=True),)
