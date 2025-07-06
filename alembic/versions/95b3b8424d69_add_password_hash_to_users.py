"""add password_hash to users

Revision ID: 95b3b8424d69
Revises: e1d8f5b9d3eb
Create Date: 2025-07-06 12:11:25.544918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95b3b8424d69'
down_revision: Union[str, Sequence[str], None] = 'e1d8f5b9d3eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "password_hash")

