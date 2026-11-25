"""Puertos de persistencia (repositorios y Unit of Work)."""
from typing import Protocol
from uuid import UUID

from app.domain.entities.fdc_analysis import FdcAnalysis
from app.domain.entities.fdc_document import FdcDocument
from app.domain.entities.project import Project


class ProjectRepositoryPort(Protocol):
    """Puerto de persistencia para Project."""

    def add(self, project: Project) -> None:
        """Agrega un nuevo proyecto a la sesión transaccional."""

    def get(self, project_id: UUID) -> Project | None:
        """Obtiene un proyecto por su identificador."""


class FdcDocumentRepositoryPort(Protocol):
    """Puerto de persistencia para FdcDocument."""

    def add(self, document: FdcDocument) -> None:
        """Agrega un nuevo documento FDC a la sesión transaccional."""

    def get(self, document_id: UUID) -> FdcDocument | None:
        """Obtiene un documento FDC por su identificador."""


class FdcAnalysisRepositoryPort(Protocol):
    """Puerto de persistencia para FdcAnalysis."""

    def add(self, analysis: FdcAnalysis) -> None:
        """Agrega un análisis FDC a la sesión transaccional."""

    def get_by_document_id(self, document_id: UUID) -> FdcAnalysis | None:
        """Obtiene el análisis asociado a un documento FDC."""


class UnitOfWorkPort(Protocol):
    """Puerto de control transaccional."""

    def commit(self) -> None:
        """Confirma los cambios pendientes en la transacción."""

    def rollback(self) -> None:
        """Revierte los cambios pendientes en la transacción."""
