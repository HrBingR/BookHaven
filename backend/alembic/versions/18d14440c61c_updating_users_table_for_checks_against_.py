"""Updating users table for checks against replay attacks

Revision ID: 18d14440c61c
Revises: 0157205d4a2e
Create Date: 2025-01-19 03:48:48.949840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18d14440c61c'
down_revision: Union[str, None] = '0157205d4a2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('last_used_otp', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'last_used_otp')
    # ### end Alembic commands ###
