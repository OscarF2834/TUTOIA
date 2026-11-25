"""Eslabón 3: Extracción preliminar de texto y verificación de legibilidad."""
from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.domain.exceptions.fdc_exceptions import UnreadableDocumentError
from app.domain.ports.document_reader_port import DocumentReaderPort


class TextReadabilityHandler(IngestionHandler):
    """Valida que el documento no esté vacío, cifrado o escaneado sin texto."""

    def __init__(self, reader: DocumentReaderPort, min_chars: int) -> None:
        super().__init__()
        self._reader = reader
        self._min_chars = min_chars

    def _process(self, ctx: FdcIngestionContext) -> None:
        extracted = self._reader.extract(ctx.content, ctx.extension)
        non_space_chars = len("".join(extracted.text.split()))
        if non_space_chars < self._min_chars:
            raise UnreadableDocumentError(
                message=(
                    "El documento no contiene suficiente texto seleccionable "
                    f"(mínimo {self._min_chars} caracteres; detectados {non_space_chars}). "
                    "Si es un PDF escaneado como imagen, conviértalo con OCR."
                ),
                context={"detected_chars": non_space_chars, "min_chars": self._min_chars},
            )
        ctx.extracted_text = extracted.text
