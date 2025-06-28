"""add_rbac

Revision ID: 3f15c1415342
Revises: cdd5c5488d31
Create Date: 2025-06-27 00:26:19.790871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f15c1415342'
down_revision: Union[str, None] = 'cdd5c5488d31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    roles = sa.Enum('admin', 'editor', 'user', name='roles')
    roles.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'users',
        sa.Column('role', roles, nullable=True)
    )
    
    # Use SQLAlchemy's table reflection and update operations
    connection = op.get_bind()
    users_table = sa.table('users',
        sa.column('role', roles),
        sa.column('is_admin', sa.Boolean())
    )
    
    # Update using SQLAlchemy's expression language with .is_() method
    connection.execute(
        users_table.update().where(users_table.c.is_admin == True).values(role='admin')
    )
    connection.execute(
        users_table.update().where(users_table.c.is_admin == False).values(role='user')
    )
    
    op.alter_column('users', 'role', nullable=False)
    op.drop_column('users', 'is_admin')


def downgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.BOOLEAN(), nullable=True))
    
    connection = op.get_bind()
    users_table = sa.table('users',
        sa.column('role', sa.Enum('admin', 'editor', 'user', name='roles')),
        sa.column('is_admin', sa.Boolean())
    )
    
    # Update using SQLAlchemy's expression language with .is_() method
    connection.execute(
        users_table.update().where(users_table.c.role == 'admin').values(is_admin=True)
    )
    connection.execute(
        users_table.update().where(users_table.c.role.in_(['user', 'editor'])).values(is_admin=False)
    )

    op.alter_column('users', 'is_admin', nullable=False)
    op.drop_column('users', 'role')
    roles = sa.Enum('admin', 'editor', 'user', name='roles')
    roles.drop(op.get_bind(), checkfirst=True)