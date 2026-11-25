"""Eslabón 1: Validación de archivo no vacío, tamaño máximo y huella SHA-256."""
import hashlib

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.domain.exceptions.fdc_exceptions import EmptyDocumentError, FileTooLargeError


class SizeIntegrityHandler(IngestionHandler):
    """Verifica que el archivo tenga contenido, no exceda el límite y calcula SHA-256."""

    def __init__(self, max_bytes: int) -> None:
        super().__init__()
        self._max_bytes = max_bytes

    def _process(self, ctx: FdcIngestionContext) -> None:
        size = len(ctx.content)
        if size == 0:
            raise EmptyDocumentError(context={"filename": ctx.filename})
        if size > self._max_bytes:
            max_mb = max(1, self._max_bytes // (1024 * 1024))
            raise FileTooLargeError(
                message=f"El archivo excede el tamaño máximo permitido de {max_mb} MB.",
                context={"max_mb": max_mb, "actual_bytes": size},
            )
        ctx.size_bytes = size
        ctx.sha256 = hashlib.sha256(ctx.content).hexdigest()
