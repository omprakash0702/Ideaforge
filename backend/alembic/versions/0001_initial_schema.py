"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── projects ───────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("problem_statement", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="CREATED"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_projects_user_id"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # ── ideas ──────────────────────────────────────────────────────────────────
    op.create_table(
        "ideas",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("parent_idea_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("generator_type", sa.String(20), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("problem", sa.Text, nullable=False),
        sa.Column("solution", sa.Text, nullable=False),
        sa.Column("target_audience", sa.Text, nullable=False),
        sa.Column("business_model", sa.Text, nullable=False),
        sa.Column("tech_stack", sa.Text, nullable=False),
        sa.Column("key_features", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("is_winner", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_ideas_project_id"
        ),
        sa.ForeignKeyConstraint(
            ["parent_idea_id"],
            ["ideas.id"],
            ondelete="SET NULL",
            name="fk_ideas_parent_idea_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ideas"),
    )
    op.create_index("ix_ideas_project_id", "ideas", ["project_id"])
    op.create_index("ix_ideas_parent_idea_id", "ideas", ["parent_idea_id"])
    op.create_index("ix_ideas_project_winner", "ideas", ["project_id", "is_winner"])

    # ── evaluations ────────────────────────────────────────────────────────────
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("idea_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("judge_type", sa.String(20), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["idea_id"], ["ideas.id"], ondelete="CASCADE", name="fk_evaluations_idea_id"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_evaluations"),
        sa.UniqueConstraint(
            "idea_id", "judge_type", name="uq_evaluation_idea_judge"
        ),
    )
    op.create_index("ix_evaluations_idea_id", "evaluations", ["idea_id"])

    # ── reports ────────────────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("winner_idea_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("markdown_report", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
            name="fk_reports_project_id",
        ),
        sa.ForeignKeyConstraint(
            ["winner_idea_id"],
            ["ideas.id"],
            ondelete="SET NULL",
            name="fk_reports_winner_idea_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
        sa.UniqueConstraint("project_id", name="uq_reports_project_id"),
    )
    op.create_index("ix_reports_project_id", "reports", ["project_id"])


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("evaluations")
    op.drop_table("ideas")
    op.drop_table("projects")
    op.drop_table("users")
