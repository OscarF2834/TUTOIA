"""create_defense_tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSON_VARIANT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Crea tablas defense_sessions y defense_turns del Módulo 2."""
    op.create_table(
        "defense_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "fdc_document_id",
            sa.Uuid(),
            sa.ForeignKey("fdc_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("jury_profile", sa.String(length=40), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("current_question_index", sa.Integer(), nullable=False),
        sa.Column("planned_questions", JSON_VARIANT, nullable=False),
        sa.Column("custom_vocabulary", JSON_VARIANT, nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("final_summary", JSON_VARIANT, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_defense_sessions_fdc_document_id", "defense_sessions", ["fdc_document_id"])

    op.create_table(
        "defense_turns",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("defense_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("is_follow_up", sa.Boolean(), nullable=False),
        sa.Column("thematic_axis", sa.String(length=40), nullable=False),
        sa.Column("aura_question_text", sa.Text(), nullable=False),
        sa.Column("student_transcript", sa.Text(), nullable=False),
        sa.Column("input_mode", sa.String(length=16), nullable=False),
        sa.Column("rubric_scores", JSON_VARIANT, nullable=False),
        sa.Column("turn_feedback", sa.Text(), nullable=False),
        sa.Column("needs_follow_up", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_defense_turns_session_id", "defense_turns", ["session_id"])


def downgrade() -> None:
    """Revierte las tablas del Módulo 2."""
    op.drop_index("ix_defense_turns_session_id", table_name="defense_turns")
    op.drop_table("defense_turns")
    op.drop_index("ix_defense_sessions_fdc_document_id", table_name="defense_sessions")
    op.drop_table("defense_sessions")
