"""add_program_phases_and_columns

Revision ID: 6f22053743a1
Revises: 06954bbd4a89
Create Date: 2026-06-10 09:21:16.438446
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401


revision = '6f22053743a1'
down_revision = '06954bbd4a89'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Create program_phases table if it does not exist
    if "program_phases" not in tables:
        op.create_table(
            "program_phases",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("program_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("phase_type", sa.String(length=50), nullable=False),
            sa.Column("start_week", sa.Integer(), nullable=False),
            sa.Column("end_week", sa.Integer(), nullable=False),
            sa.Column("volume_multiplier", sa.Float(), nullable=False),
            sa.Column("intensity_multiplier", sa.Float(), nullable=False),
            sa.Column("rpe_modifier", sa.Integer(), nullable=False),
            sa.Column("is_deload", sa.Boolean(), nullable=False),
            sa.Column("notes", sa.String(length=1000), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["program_id"], ["training_programs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_program_phases_program_id"), "program_phases", ["program_id"], unique=False)

    # 2. Add columns to training_programs if they do not exist
    if "training_programs" in tables:
        tp_cols = [c["name"] for c in inspector.get_columns("training_programs")]
        if "generation_strategy" not in tp_cols:
            op.add_column("training_programs", sa.Column("generation_strategy", sa.String(length=50), nullable=False, server_default="full_program"))
        if "current_phase" not in tp_cols:
            op.add_column("training_programs", sa.Column("current_phase", sa.String(length=50), nullable=True))
        if "total_scheduled_workouts" not in tp_cols:
            op.add_column("training_programs", sa.Column("total_scheduled_workouts", sa.Integer(), nullable=False, server_default="0"))
        if "completed_workouts_count" not in tp_cols:
            op.add_column("training_programs", sa.Column("completed_workouts_count", sa.Integer(), nullable=False, server_default="0"))

    # 3. Add columns to program_workout_instances if they do not exist
    if "program_workout_instances" in tables:
        pwi_cols = [c["name"] for c in inspector.get_columns("program_workout_instances")]
        if "planned_workout_plan_id" not in pwi_cols:
            op.add_column("program_workout_instances", sa.Column("planned_workout_plan_id", sa.Uuid(), nullable=True))
        if "adjusted_workout_plan_id" not in pwi_cols:
            op.add_column("program_workout_instances", sa.Column("adjusted_workout_plan_id", sa.Uuid(), nullable=True))
        if "original_scheduled_date" not in pwi_cols:
            op.add_column("program_workout_instances", sa.Column("original_scheduled_date", sa.Date(), nullable=True))
        if "completed_at" not in pwi_cols:
            op.add_column("program_workout_instances", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
        if "adjustment_reason" not in pwi_cols:
            op.add_column("program_workout_instances", sa.Column("adjustment_reason", sa.String(length=255), nullable=True))

        # Add foreign keys and indexes
        fks = [fk["name"] for fk in inspector.get_foreign_keys("program_workout_instances")]
        if "fk_program_workout_instances_planned_workout_plan" not in fks:
            op.create_foreign_key(
                "fk_program_workout_instances_planned_workout_plan",
                "program_workout_instances",
                "workout_plans",
                ["planned_workout_plan_id"],
                ["id"],
            )
        if "fk_program_workout_instances_adjusted_workout_plan" not in fks:
            op.create_foreign_key(
                "fk_program_workout_instances_adjusted_workout_plan",
                "program_workout_instances",
                "workout_plans",
                ["adjusted_workout_plan_id"],
                ["id"],
            )

        idxs = [idx["name"] for idx in inspector.get_indexes("program_workout_instances")]
        if "ix_program_workout_instances_planned_workout_plan_id" not in idxs:
            op.create_index(
                op.f("ix_program_workout_instances_planned_workout_plan_id"),
                "program_workout_instances",
                ["planned_workout_plan_id"],
                unique=False,
            )
        if "ix_program_workout_instances_adjusted_workout_plan_id" not in idxs:
            op.create_index(
                op.f("ix_program_workout_instances_adjusted_workout_plan_id"),
                "program_workout_instances",
                ["adjusted_workout_plan_id"],
                unique=False,
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Drop foreign keys and indexes from program_workout_instances
    if "program_workout_instances" in tables:
        fks = [fk["name"] for fk in inspector.get_foreign_keys("program_workout_instances")]
        if "fk_program_workout_instances_adjusted_workout_plan" in fks:
            op.drop_constraint("fk_program_workout_instances_adjusted_workout_plan", "program_workout_instances", type_="foreignkey")
        if "fk_program_workout_instances_planned_workout_plan" in fks:
            op.drop_constraint("fk_program_workout_instances_planned_workout_plan", "program_workout_instances", type_="foreignkey")

        idxs = [idx["name"] for idx in inspector.get_indexes("program_workout_instances")]
        if "ix_program_workout_instances_adjusted_workout_plan_id" in idxs:
            op.drop_index(op.f("ix_program_workout_instances_adjusted_workout_plan_id"), table_name="program_workout_instances")
        if "ix_program_workout_instances_planned_workout_plan_id" in idxs:
            op.drop_index(op.f("ix_program_workout_instances_planned_workout_plan_id"), table_name="program_workout_instances")

        pwi_cols = [c["name"] for c in inspector.get_columns("program_workout_instances")]
        if "adjustment_reason" in pwi_cols:
            op.drop_column("program_workout_instances", "adjustment_reason")
        if "completed_at" in pwi_cols:
            op.drop_column("program_workout_instances", "completed_at")
        if "original_scheduled_date" in pwi_cols:
            op.drop_column("program_workout_instances", "original_scheduled_date")
        if "adjusted_workout_plan_id" in pwi_cols:
            op.drop_column("program_workout_instances", "adjusted_workout_plan_id")
        if "planned_workout_plan_id" in pwi_cols:
            op.drop_column("program_workout_instances", "planned_workout_plan_id")

    # 2. Drop columns from training_programs
    if "training_programs" in tables:
        tp_cols = [c["name"] for c in inspector.get_columns("training_programs")]
        if "completed_workouts_count" in tp_cols:
            op.drop_column("training_programs", "completed_workouts_count")
        if "total_scheduled_workouts" in tp_cols:
            op.drop_column("training_programs", "total_scheduled_workouts")
        if "current_phase" in tp_cols:
            op.drop_column("training_programs", "current_phase")
        if "generation_strategy" in tp_cols:
            op.drop_column("training_programs", "generation_strategy")

    # 3. Drop program_phases table
    if "program_phases" in tables:
        op.drop_table("program_phases")
