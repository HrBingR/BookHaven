"""New epubmetadata table indexes

Revision ID: 12285fde0fd3
Revises: 09c9fb1450dd
Create Date: 2025-02-08 05:50:18.768116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12285fde0fd3'
down_revision: Union[str, None] = '09c9fb1450dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('author_title_index_series_idx', 'epub_metadata', ['authors', 'series', 'seriesindex', 'title'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('author_title_index_series_idx', table_name='epub_metadata')
    # ### end Alembic commands ###
