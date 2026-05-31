"""Update workout lifecycle schema

Revision ID: 8d6b7d0f4b1a
Revises: 59f0a3a6d305
Create Date: 2026-05-31 23:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8d6b7d0f4b1a"
down_revision = "59f0a3a6d305"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workout_logs",
        sa.Column("total_volume", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("workout_logs", sa.Column("calories_burned", sa.Float(), nullable=True))
    op.add_column("workout_logs", sa.Column("avg_heart_rate", sa.Float(), nullable=True))

    op.alter_column("workout_set_logs", "reps_completed", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "workout_set_logs",
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "workout_set_logs",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_unique_constraint(
        "uq_workout_set_logs_log_exercise_set",
        "workout_set_logs",
        ["workout_log_id", "workout_plan_exercise_id", "set_number"],
    )

    op.alter_column(
        "workout_feedback",
        "difficulty_feedback",
        existing_type=sa.String(length=50),
        nullable=True,
    )
    op.add_column("workout_feedback", sa.Column("energy_after", sa.Integer(), nullable=True))
    op.add_column(
        "workout_feedback",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.alter_column("workout_logs", "total_volume", server_default=None)
    op.alter_column("workout_set_logs", "completed", server_default=None)
    op.alter_column("workout_set_logs", "updated_at", server_default=None)
    op.alter_column("workout_feedback", "updated_at", server_default=None)


def downgrade() -> None:
    op.drop_column("workout_feedback", "updated_at")
    op.drop_column("workout_feedback", "energy_after")
    op.alter_column(
        "workout_feedback",
        "difficulty_feedback",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.drop_constraint(
        "uq_workout_set_logs_log_exercise_set", "workout_set_logs", type_="unique"
    )
    op.drop_column("workout_set_logs", "updated_at")
    op.drop_column("workout_set_logs", "completed")
    op.alter_column("workout_set_logs", "reps_completed", existing_type=sa.Integer(), nullable=False)

    op.drop_column("workout_logs", "avg_heart_rate")
    op.drop_column("workout_logs", "calories_burned")
    op.drop_column("workout_logs", "total_volume")
