"""add_workout_heart_rate_range

Revision ID: 8f5a1c2d9b77
Revises: 6c2459993615
Create Date: 2026-06-10 15:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "8f5a1c2d9b77"
down_revision = "6c2459993615"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "workout_logs" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("workout_logs")}
    if "max_heart_rate" not in columns:
        op.add_column(
            "workout_logs",
            sa.Column("max_heart_rate", sa.Float(), nullable=True),
        )
    if "min_heart_rate" not in columns:
        op.add_column(
            "workout_logs",
            sa.Column("min_heart_rate", sa.Float(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "workout_logs" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("workout_logs")}
    if "min_heart_rate" in columns:
        op.drop_column("workout_logs", "min_heart_rate")
    if "max_heart_rate" in columns:
        op.drop_column("workout_logs", "max_heart_rate")
