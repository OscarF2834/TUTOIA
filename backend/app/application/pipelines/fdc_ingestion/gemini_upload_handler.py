"""Eslabón 5: Indexación del documento validado en Gemini Files API."""
from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.domain.ports.ai_fdc_analyzer_port import AiFdcAnalyzerPort


class GeminiUploadHandler(IngestionHandler):
    """Sube el documento al motor IA tras superar todas las validaciones previas."""

    def __init__(self, analyzer: AiFdcAnalyzerPort) -> None:
        super().__init__()
        self._analyzer = analyzer

    def _process(self, ctx: FdcIngestionContext) -> None:
        ctx.remote_file = self._analyzer.upload_document(
            content=ctx.content,
            mime_type=ctx.mime_type,
            display_name=ctx.filename,
            extracted_text=ctx.extracted_text,
        )
