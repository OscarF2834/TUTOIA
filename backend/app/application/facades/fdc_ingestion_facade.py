"""Facade de aplicación para ingesta y consulta de documentos FDC."""
from uuid import UUID

from app.application.dto.fdc_ingestion_dto import FdcDocumentView, FdcUploadCommand
from app.application.use_cases.get_fdc_analysis import GetFdcAnalysisUseCase
from app.application.use_cases.ingest_and_analyze_fdc import IngestAndAnalyzeFdcUseCase


class FdcIngestionFacade:
    """Punto único de entrada de la capa de aplicación para routers FDC."""

    def __init__(
        self,
        ingest_use_case: IngestAndAnalyzeFdcUseCase,
        get_use_case: GetFdcAnalysisUseCase,
    ) -> None:
        self._ingest_use_case = ingest_use_case
        self._get_use_case = get_use_case

    def upload(self, cmd: FdcUploadCommand) -> FdcDocumentView:
        """Orquesta la carga, validación, indexación y análisis del FDC."""
        return self._ingest_use_case.execute(cmd)

    def get(self, document_id: UUID) -> FdcDocumentView:
        """Consulta el análisis persistido de un documento FDC."""
        return self._get_use_case.execute(document_id)
