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

    def author_first_names(self) -> list[str]:
        """Extrae el primer nombre limpio de cada integrante registrado en el proyecto."""
        names: list[str] = []
        for author in self.authors:
            raw = author.full_name.strip()
            if not raw:
                continue
            token = raw.split()[0].strip(",.;:")
            if token:
                names.append(token.capitalize())
        return names

    def is_team(self) -> bool:
        """Indica si el trabajo de grado cuenta con dos o más sustentantes."""
        return len(self.author_first_names()) > 1

    def formatted_authors_greeting(self) -> str:
        """Formatea saludo natural para 1, 2 o más sustentantes (ej. 'Pedro y Oscar')."""
        names = self.author_first_names()
        if not names:
            return "estudiante"
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} y {names[1]}"
        return f"{', '.join(names[:-1])} y {names[-1]}"
