"""Modelo ORM para la tabla projects."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, JsonVariant


class ProjectModel(Base):
    """Representación relacional del expediente de trabajo de grado."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(350), nullable=False)
    academic_program: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    modality: Mapped[str] = mapped_column(String(50), nullable=False)
    authors: Mapped[list[dict]] = mapped_column(JsonVariant, nullable=False)
    director_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ANALYZED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
