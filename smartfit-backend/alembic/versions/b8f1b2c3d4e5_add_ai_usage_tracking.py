"""Add AI usage tracking and request logging fields

Revision ID: b8f1b2c3d4e5
Revises: e24cb468487f
Create Date: 2026-06-01 11:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "b8f1b2c3d4e5"
down_revision = "486a84cd5034"
branch_labels = None
depends_on = None


def _json_type(dialect_name: str):
    if dialect_name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _json_default(dialect_name: str):
    if dialect_name == "postgresql":
        return sa.text("'{}'::jsonb")
    return sa.text("'{}'")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect_name = bind.dialect.name
    tables = set(inspector.get_table_names())
    json_type = _json_type(dialect_name)
    json_default = _json_default(dialect_name)

    if "ai_requests" not in tables:
        op.create_table(
            "ai_requests",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("workout_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("request_type", sa.String(length=50), nullable=False),
            sa.Column(
                "provider",
                sa.String(length=50),
                nullable=False,
                server_default="gemini",
            ),
            sa.Column(
                "model_name", sa.String(length=100), nullable=False, server_default=""
            ),
            sa.Column("generation_mode", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("prompt", sa.String(length=4000), nullable=True),
            sa.Column("response", sa.String(length=12000), nullable=True),
            sa.Column(
                "input_payload", json_type, nullable=False, server_default=json_default
            ),
            sa.Column(
                "output_payload", json_type, nullable=False, server_default=json_default
            ),
            sa.Column("error_code", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.String(length=4000), nullable=True),
            sa.Column(
                "fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column(
                "metadata", json_type, nullable=False, server_default=json_default
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["workout_plan_id"], ["workout_plans.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_ai_requests_user_id"), "ai_requests", ["user_id"], unique=False
        )
        op.create_index(
            op.f("ix_ai_requests_workout_plan_id"),
            "ai_requests",
            ["workout_plan_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_ai_requests_request_type"),
            "ai_requests",
            ["request_type"],
            unique=False,
        )
        op.create_index(
            op.f("ix_ai_requests_status"), "ai_requests", ["status"], unique=False
        )
    else:
        columns = {column["name"] for column in inspector.get_columns("ai_requests")}
        if "workout_plan_id" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column(
                    "workout_plan_id", postgresql.UUID(as_uuid=True), nullable=True
                ),
            )
            op.create_index(
                op.f("ix_ai_requests_workout_plan_id"),
                "ai_requests",
                ["workout_plan_id"],
                unique=False,
            )
            op.create_foreign_key(
                "fk_ai_requests_workout_plan_id_workout_plans",
                "ai_requests",
                "workout_plans",
                ["workout_plan_id"],
                ["id"],
            )
        if "provider" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column(
                    "provider",
                    sa.String(length=50),
                    nullable=False,
                    server_default="gemini",
                ),
            )
        if "model_name" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column(
                    "model_name",
                    sa.String(length=100),
                    nullable=False,
                    server_default="",
                ),
            )
        if "generation_mode" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column("generation_mode", sa.String(length=50), nullable=True),
            )
        if "input_payload" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column(
                    "input_payload",
                    json_type,
                    nullable=False,
                    server_default=json_default,
                ),
            )
        if "output_payload" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column(
                    "output_payload",
                    json_type,
                    nullable=False,
                    server_default=json_default,
                ),
            )
        if "error_code" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column("error_code", sa.String(length=100), nullable=True),
            )
        if "error_message" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column("error_message", sa.String(length=4000), nullable=True),
            )
        if "fallback_used" not in columns:
            op.add_column(
                "ai_requests",
                sa.Column(
                    "fallback_used",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
            )
        if "latency_ms" not in columns:
            op.add_column(
                "ai_requests", sa.Column("latency_ms", sa.Integer(), nullable=True)
            )

    if "ai_chat_messages" not in tables:
        op.create_table(
            "ai_chat_messages",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("ai_request_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("content", sa.String(length=4000), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_ai_chat_messages_ai_request_id"),
            "ai_chat_messages",
            ["ai_request_id"],
            unique=False,
        )

    if "ai_usage_daily" not in tables:
        op.create_table(
            "ai_usage_daily",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column(
                "ai_workout_count", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column(
                "ai_chat_count", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column(
                "ai_replacement_count", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column(
                "ai_weekly_report_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "total_ai_count", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "date", name="uq_ai_usage_daily_user_date"),
        )
        op.create_index(
            op.f("ix_ai_usage_daily_user_id"),
            "ai_usage_daily",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_ai_usage_daily_date"), "ai_usage_daily", ["date"], unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "ai_usage_daily" in tables:
        op.drop_index(op.f("ix_ai_usage_daily_date"), table_name="ai_usage_daily")
        op.drop_index(op.f("ix_ai_usage_daily_user_id"), table_name="ai_usage_daily")
        op.drop_table("ai_usage_daily")

    if "ai_chat_messages" in tables:
        op.drop_index(
            op.f("ix_ai_chat_messages_ai_request_id"), table_name="ai_chat_messages"
        )
        op.drop_table("ai_chat_messages")

    if "ai_requests" in tables:
        columns = {column["name"] for column in inspector.get_columns("ai_requests")}
        if "latency_ms" in columns:
            op.drop_column("ai_requests", "latency_ms")
        if "fallback_used" in columns:
            op.drop_column("ai_requests", "fallback_used")
        if "error_message" in columns:
            op.drop_column("ai_requests", "error_message")
        if "error_code" in columns:
            op.drop_column("ai_requests", "error_code")
        if "output_payload" in columns:
            op.drop_column("ai_requests", "output_payload")
        if "input_payload" in columns:
            op.drop_column("ai_requests", "input_payload")
        if "generation_mode" in columns:
            op.drop_column("ai_requests", "generation_mode")
        if "model_name" in columns:
            op.drop_column("ai_requests", "model_name")
        if "provider" in columns:
            op.drop_column("ai_requests", "provider")
        if "workout_plan_id" in columns:
            op.drop_constraint(
                "fk_ai_requests_workout_plan_id_workout_plans",
                "ai_requests",
                type_="foreignkey",
            )
            op.drop_index(
                op.f("ix_ai_requests_workout_plan_id"), table_name="ai_requests"
            )
            op.drop_column("ai_requests", "workout_plan_id")
