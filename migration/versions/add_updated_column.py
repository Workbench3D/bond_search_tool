"""add updated column

Revision ID: f57551b50396
Revises: c5c0cd5eb319
Create Date: 2024-03-02 21:30:49.265348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f57551b50396'
down_revision: Union[str, None] = 'c5c0cd5eb319'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bonds', sa.Column('updated', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bonds', 'updated')
    # ### end Alembic commands ###
