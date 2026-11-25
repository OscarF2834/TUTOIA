"""Caso de uso: consulta de documento FDC y su diagnóstico asociado."""
from uuid import UUID

from app.application.dto.fdc_ingestion_dto import FdcDocumentView
from app.domain.exceptions.fdc_exceptions import FdcDocumentNotFoundError
from app.domain.ports.repositories import (
    FdcAnalysisRepositoryPort,
    FdcDocumentRepositoryPort,
    ProjectRepositoryPort,
)


class GetFdcAnalysisUseCase:
    """Recupera la vista completa de proyecto, documento y análisis."""

    def __init__(
        self,
        project_repo: ProjectRepositoryPort,
        document_repo: FdcDocumentRepositoryPort,
        analysis_repo: FdcAnalysisRepositoryPort,
    ) -> None:
        self._project_repo = project_repo
        self._document_repo = document_repo
        self._analysis_repo = analysis_repo

    def execute(self, document_id: UUID) -> FdcDocumentView:
        """Retorna FdcDocumentView o lanza FdcDocumentNotFoundError."""
        document = self._document_repo.get(document_id)
        if document is None:
            raise FdcDocumentNotFoundError(
                message=f"No se encontró el documento FDC '{document_id}'.",
                context={"document_id": str(document_id)},
            )
        project = self._project_repo.get(document.project_id)
        analysis = self._analysis_repo.get_by_document_id(document.id)
        if project is None or analysis is None:
            raise FdcDocumentNotFoundError(
                message=f"Los datos asociados al documento '{document_id}' están incompletos.",
                context={"document_id": str(document_id)},
            )
        return FdcDocumentView(project=project, document=document, analysis=analysis)
