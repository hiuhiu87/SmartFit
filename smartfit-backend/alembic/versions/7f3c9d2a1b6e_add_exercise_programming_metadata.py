"""Add exercise programming metadata

Revision ID: 7f3c9d2a1b6e
Revises: 9b3064af791c
Create Date: 2026-06-02 21:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401

revision = "7f3c9d2a1b6e"
down_revision = "9b3064af791c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column(
            "movement_pattern",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=True,
        ),
    )
    op.add_column(
        "exercises",
        sa.Column(
            "exercise_role", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
    )
    op.add_column(
        "exercises",
        sa.Column(
            "fatigue_level", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
    )
    op.add_column(
        "exercises",
        sa.Column(
            "joint_stress", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
    )
    op.add_column(
        "exercises",
        sa.Column(
            "substitution_group",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_exercises_movement_pattern"),
        "exercises",
        ["movement_pattern"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exercises_exercise_role"), "exercises", ["exercise_role"], unique=False
    )
    op.create_index(
        op.f("ix_exercises_fatigue_level"), "exercises", ["fatigue_level"], unique=False
    )
    op.create_index(
        op.f("ix_exercises_joint_stress"), "exercises", ["joint_stress"], unique=False
    )
    op.create_index(
        op.f("ix_exercises_substitution_group"),
        "exercises",
        ["substitution_group"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exercises_substitution_group"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_joint_stress"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_fatigue_level"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_exercise_role"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_movement_pattern"), table_name="exercises")
    op.drop_column("exercises", "substitution_group")
    op.drop_column("exercises", "joint_stress")
    op.drop_column("exercises", "fatigue_level")
    op.drop_column("exercises", "exercise_role")
    op.drop_column("exercises", "movement_pattern")
