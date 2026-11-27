"""Modelo ORM para la tabla defense_sessions."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, JsonVariant


class DefenseSessionModel(Base):
    """Representación relacional de una sesión de sustentación oral."""

    __tablename__ = "defense_sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    fdc_document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fdc_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jury_profile: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    planned_questions: Mapped[list[dict]] = mapped_column(JsonVariant, nullable=False)
    custom_vocabulary: Mapped[list[str]] = mapped_column(JsonVariant, nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_summary: Mapped[dict | None] = mapped_column(JsonVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
