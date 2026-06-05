"""Add training style preferences.

Revision ID: c4a91f72e6d3
Revises: 66d8843d18a2
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa

revision = "c4a91f72e6d3"
down_revision = "66d8843d18a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "training_style",
            sa.String(length=50),
            nullable=False,
            server_default="balanced",
        ),
    )
    op.add_column(
        "training_programs",
        sa.Column(
            "training_style",
            sa.String(length=50),
            nullable=False,
            server_default="balanced",
        ),
    )


def downgrade() -> None:
    op.drop_column("training_programs", "training_style")
    op.drop_column("user_profiles", "training_style")
