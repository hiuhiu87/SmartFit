"""Add training program tables.

Revision ID: a1f6c2d8e4b0
Revises: e3b0c6458a2e
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "a1f6c2d8e4b0"
down_revision = "e3b0c6458a2e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_programs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("goal", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column(
            "training_level",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
        ),
        sa.Column("duration_weeks", sa.Integer(), nullable=False),
        sa.Column("days_per_week", sa.Integer(), nullable=False),
        sa.Column("session_duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "preferred_split",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
        ),
        sa.Column(
            "status", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("current_week", sa.Integer(), nullable=False),
        sa.Column("current_day_index", sa.Integer(), nullable=False),
        sa.Column(
            "generation_mode",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
        ),
        sa.Column("focus_areas", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_id", "goal", "status", "start_date", "end_date"):
        op.create_index(
            op.f(f"ix_training_programs_{column}"),
            "training_programs",
            [column],
            unique=False,
        )

    op.create_table(
        "program_workout_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column(
            "title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column(
            "focus_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column(
            "workout_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["training_programs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "program_id", "day_index", name="uq_program_workout_templates_day"
        ),
    )
    op.create_index(
        op.f("ix_program_workout_templates_program_id"),
        "program_workout_templates",
        ["program_id"],
        unique=False,
    )

    op.create_table(
        "program_template_slots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("program_workout_template_id", sa.Uuid(), nullable=False),
        sa.Column("slot_order", sa.Integer(), nullable=False),
        sa.Column(
            "slot_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column("movement_patterns", sa.JSON(), nullable=False),
        sa.Column("primary_muscles", sa.JSON(), nullable=False),
        sa.Column("exercise_roles", sa.JSON(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("base_sets", sa.Integer(), nullable=False),
        sa.Column(
            "base_reps", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column("base_rest_seconds", sa.Integer(), nullable=False),
        sa.Column("base_rpe", sa.Integer(), nullable=False),
        sa.Column(
            "progression_rule",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["program_workout_template_id"], ["program_workout_templates.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "program_workout_template_id",
            "slot_order",
            name="uq_program_template_slots_order",
        ),
    )
    op.create_index(
        op.f("ix_program_template_slots_program_workout_template_id"),
        "program_template_slots",
        ["program_workout_template_id"],
        unique=False,
    )

    op.create_table(
        "program_workout_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("program_workout_template_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("actual_workout_plan_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column(
            "readiness_adjustment",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actual_workout_plan_id"], ["workout_plans.id"]),
        sa.ForeignKeyConstraint(["program_id"], ["training_programs.id"]),
        sa.ForeignKeyConstraint(
            ["program_workout_template_id"], ["program_workout_templates.id"]
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "program_id",
            "week_number",
            "day_index",
            name="uq_program_workout_instances_position",
        ),
    )
    for column in (
        "program_id",
        "program_workout_template_id",
        "user_id",
        "scheduled_date",
        "actual_workout_plan_id",
        "status",
    ):
        op.create_index(
            op.f(f"ix_program_workout_instances_{column}"),
            "program_workout_instances",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("program_workout_instances")
    op.drop_table("program_template_slots")
    op.drop_table("program_workout_templates")
    op.drop_table("training_programs")
