"""Modelo ORM para la tabla defense_turns."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, JsonVariant


class DefenseTurnModel(Base):
    """Representación relacional de un turno evaluado en la sustentación."""

    __tablename__ = "defense_turns"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("defense_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    thematic_axis: Mapped[str] = mapped_column(String(40), nullable=False)
    aura_question_text: Mapped[str] = mapped_column(Text, nullable=False)
    student_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    rubric_scores: Mapped[dict] = mapped_column(JsonVariant, nullable=False)
    turn_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    needs_follow_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
