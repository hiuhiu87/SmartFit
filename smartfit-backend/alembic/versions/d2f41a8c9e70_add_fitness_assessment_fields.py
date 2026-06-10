"""Add fitness assessment fields.

Revision ID: d2f41a8c9e70
Revises: 734790b99211
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d2f41a8c9e70"
down_revision = "734790b99211"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("lifestyle_type", sa.Text()))
    op.add_column("user_profiles", sa.Column("sitting_hours_per_day", sa.Float()))
    op.add_column("user_profiles", sa.Column("training_history", sa.Text()))
    op.add_column("user_profiles", sa.Column("months_inactive", sa.Integer()))
    op.add_column(
        "user_profiles",
        sa.Column(
            "movement_limitations",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "pain_areas",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "pain_movements",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "pain_movements")
    op.drop_column("user_profiles", "pain_areas")
    op.drop_column("user_profiles", "movement_limitations")
    op.drop_column("user_profiles", "months_inactive")
    op.drop_column("user_profiles", "training_history")
    op.drop_column("user_profiles", "sitting_hours_per_day")
    op.drop_column("user_profiles", "lifestyle_type")
