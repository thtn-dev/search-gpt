"""Initial

Revision ID: 098bde3044d4
Revises: 
Create Date: 2025-05-17 00:19:31.745114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '098bde3044d4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
