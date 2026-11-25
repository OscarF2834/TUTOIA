"""create_fdc_core_tables

Revision ID: 0001
Revises:
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSON_VARIANT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Crea tablas iniciales projects, fdc_documents y fdc_analyses."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=350), nullable=False),
        sa.Column("academic_program", sa.String(length=150), nullable=False),
        sa.Column("modality", sa.String(length=50), nullable=False),
        sa.Column("authors", JSON_VARIANT, nullable=False),
        sa.Column("director_name", sa.String(length=150), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_academic_program", "projects", ["academic_program"])

    op.create_table(
        "fdc_documents",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fdc_type", sa.String(length=20), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("gemini_file_name", sa.String(length=120), nullable=True),
        sa.Column("gemini_file_uri", sa.String(length=500), nullable=True),
        sa.Column("gemini_file_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingestion_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fdc_documents_project_id", "fdc_documents", ["project_id"])
    op.create_index("ix_fdc_documents_sha256_hash", "fdc_documents", ["sha256_hash"])

    op.create_table(
        "fdc_analyses",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "fdc_document_id",
            sa.Uuid(),
            sa.ForeignKey("fdc_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("strategy_name", sa.String(length=80), nullable=False),
        sa.Column("model_name", sa.String(length=80), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("academic_synthesis", JSON_VARIANT, nullable=False),
        sa.Column("coherence_findings", JSON_VARIANT, nullable=False),
        sa.Column("detected_gaps", JSON_VARIANT, nullable=False),
        sa.Column("execution_metrics", JSON_VARIANT, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fdc_document_id", name="uq_fdc_analyses_fdc_document_id"),
    )
    op.create_index("ix_fdc_analyses_fdc_document_id", "fdc_analyses", ["fdc_document_id"])


def downgrade() -> None:
    """Revierte las tablas iniciales del módulo FDC."""
    op.drop_index("ix_fdc_analyses_fdc_document_id", table_name="fdc_analyses")
    op.drop_table("fdc_analyses")
    op.drop_index("ix_fdc_documents_sha256_hash", table_name="fdc_documents")
    op.drop_index("ix_fdc_documents_project_id", table_name="fdc_documents")
    op.drop_table("fdc_documents")
    op.drop_index("ix_projects_academic_program", table_name="projects")
    op.drop_table("projects")
