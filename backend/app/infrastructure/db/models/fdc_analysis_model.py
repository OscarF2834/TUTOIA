"""Modelo ORM para la tabla fdc_analyses."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, JsonVariant


class FdcAnalysisModel(Base):
    """Representación relacional del análisis estructurado de un documento FDC."""

    __tablename__ = "fdc_analyses"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    fdc_document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fdc_documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    academic_synthesis: Mapped[dict] = mapped_column(JsonVariant, nullable=False)
    coherence_findings: Mapped[dict] = mapped_column(JsonVariant, nullable=False)
    detected_gaps: Mapped[list[dict]] = mapped_column(JsonVariant, nullable=False)
    execution_metrics: Mapped[dict] = mapped_column(JsonVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
