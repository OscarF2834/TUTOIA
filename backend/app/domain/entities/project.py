"""Entidad Project y objetos de valor asociados."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domain.entities.fdc_document import Modality


class ProjectStatus(StrEnum):
    """Estados del proyecto de grado en la plataforma."""

    DRAFT = "DRAFT"
    ANALYZED = "ANALYZED"
    IN_DEFENSE = "IN_DEFENSE"
    EVALUATED = "EVALUATED"


@dataclass(frozen=True)
class Author:
    """Autor sustentante del trabajo de grado."""

    full_name: str
    student_code: str | None = None


@dataclass
class Project:
    """Agregado raíz del expediente académico de trabajo de grado."""

    id: UUID
    title: str
    academic_program: str
    modality: Modality
    authors: list[Author]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    director_name: str | None = None
