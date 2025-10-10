"""create invoices table

Revision ID: 93d458957a99
Revises: 3bb87b199ae3
Create Date: 2025-10-08 20:13:39.142226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93d458957a99'
down_revision: Union[str, Sequence[str], None] = '3bb87b199ae3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
