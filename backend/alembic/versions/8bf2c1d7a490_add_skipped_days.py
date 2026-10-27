"""add skipped supplement days

Revision ID: 8bf2c1d7a490
Revises: d257318ca581
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8bf2c1d7a490"
down_revision: Union[str, Sequence[str], None] = "d257318ca581"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skipped_days",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplement_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["supplement_id"], ["supplements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplement_id", "date", name="uq_skipped_day_supplement_date"),
    )
    op.create_index(op.f("ix_skipped_days_id"), "skipped_days", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_skipped_days_id"), table_name="skipped_days")
    op.drop_table("skipped_days")
