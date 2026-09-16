"""replace doses_per_day with dose frequency fields

Revision ID: 3394a6849619
Revises: 5a4fcd932c4d
Create Date: 2026-09-15 23:59:52.537510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3394a6849619'
down_revision: Union[str, Sequence[str], None] = '5a4fcd932c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adds the new frequency fields and backfills them from the existing
    doses_per_day column before dropping it, so existing rows aren't lost
    or left with invalid data. Old doses_per_day=N maps exactly onto
    dose_amount=1, frequency_count=N, frequency_unit='day' — the same
    daily rate, expressed the new way.
    """
    # 1. Add nullable first — can't add NOT NULL columns to a table that
    #    already has rows without a value to fill them with.
    op.add_column('supplements', sa.Column('dose_amount', sa.Float(), nullable=True))
    op.add_column('supplements', sa.Column('frequency_count', sa.Float(), nullable=True))
    op.add_column('supplements', sa.Column('frequency_unit', sa.String(), nullable=True))

    # 2. Backfill existing rows from the old column.
    op.execute(
        "UPDATE supplements SET dose_amount = 1.0, frequency_count = doses_per_day, frequency_unit = 'day'"
    )

    # 3. Now that every row has a value, enforce NOT NULL.
    op.alter_column('supplements', 'dose_amount', nullable=False)
    op.alter_column('supplements', 'frequency_count', nullable=False)
    op.alter_column('supplements', 'frequency_unit', nullable=False)

    # 4. Old column is no longer needed.
    op.drop_column('supplements', 'doses_per_day')


def downgrade() -> None:
    """Reverses the above: doses_per_day = dose_amount * frequency_count / days_per_unit('day') = dose_amount * frequency_count (day unit only assumed)."""
    op.add_column('supplements', sa.Column('doses_per_day', sa.Float(), nullable=True))
    op.execute("UPDATE supplements SET doses_per_day = dose_amount * frequency_count")
    op.alter_column('supplements', 'doses_per_day', nullable=False)
    op.drop_column('supplements', 'frequency_unit')
    op.drop_column('supplements', 'frequency_count')
    op.drop_column('supplements', 'dose_amount')
