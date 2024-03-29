"""initial

Revision ID: c5c0cd5eb319
Revises: 
Create Date: 2024-03-02 21:13:33.721777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c5c0cd5eb319"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "bonds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shortname", sa.String(), nullable=False),
        sa.Column("secid", sa.String(), nullable=False),
        sa.Column("matdate", sa.Date(), nullable=False),
        sa.Column("face_unit", sa.String(), nullable=False),
        sa.Column("list_level", sa.Integer(), nullable=False),
        sa.Column("days_to_redemption", sa.Integer(), nullable=False),
        sa.Column("face_value", sa.Float(), nullable=False),
        sa.Column("coupon_frequency", sa.Integer(), nullable=False),
        sa.Column("coupon_date", sa.Date(), nullable=False),
        sa.Column("coupon_percent", sa.Float(), nullable=False),
        sa.Column("coupon_value", sa.Float(), nullable=False),
        sa.Column("highrisk", sa.Boolean(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("accint", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("moex_yield", sa.Float(), nullable=False),
        sa.Column("amortizations", sa.Boolean(), nullable=False),
        sa.Column("floater", sa.Boolean(), nullable=False),
        sa.Column("sum_coupon", sa.Float(), nullable=False),
        sa.Column("year_percent", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bonds_id"), "bonds", ["id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_bonds_id"), table_name="bonds")
    op.drop_table("bonds")
    # ### end Alembic commands ###
