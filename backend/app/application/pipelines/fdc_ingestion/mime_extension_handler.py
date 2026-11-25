"""Eslabón 2: Validación de extensión y firma mágica real (.pdf / .docx)."""
import io
import zipfile
from pathlib import Path

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.domain.exceptions.fdc_exceptions import UnsupportedDocumentFormatError

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class MimeExtensionHandler(IngestionHandler):
    """Valida extensión permitida y magic bytes reales del binario."""

    def _process(self, ctx: FdcIngestionContext) -> None:
        ext = Path(ctx.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedDocumentFormatError(
                message=f"Formato '{ext or 'desconocido'}' no permitido. Cargue un archivo .pdf o .docx.",
                context={"extension": ext},
            )

        if ext == ".pdf":
            if not ctx.content.startswith(b"%PDF-"):
                raise UnsupportedDocumentFormatError(
                    message="El archivo .pdf no posee una cabecera PDF válida.",
                    context={"extension": ext},
                )
            ctx.extension = ext
            ctx.mime_type = PDF_MIME
            return

        if not self._is_valid_docx(ctx.content):
            raise UnsupportedDocumentFormatError(
                message="El archivo .docx no corresponde a un documento Word OOXML válido.",
                context={"extension": ext},
            )
        ctx.extension = ext
        ctx.mime_type = DOCX_MIME

    @staticmethod
    def _is_valid_docx(content: bytes) -> bool:
        if not content.startswith(b"PK\x03\x04"):
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
                return "word/document.xml" in archive.namelist()
        except zipfile.BadZipFile:
            return False
