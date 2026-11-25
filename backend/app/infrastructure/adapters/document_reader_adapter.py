"""Adaptador unificado para extracción preliminar de texto en PDF y DOCX."""
import io

import docx
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.domain.exceptions.fdc_exceptions import (
    CorruptedDocumentError,
    UnreadableDocumentError,
    UnsupportedDocumentFormatError,
)
from app.domain.ports.document_reader_port import ExtractedDocument


class DocumentReaderAdapter:
    """Implementa DocumentReaderPort sobre pypdf y python-docx."""

    def extract(self, content: bytes, extension: str) -> ExtractedDocument:
        """Extrae texto verificable de PDF o DOCX según extensión."""
        ext = extension.lower()
        if ext == ".pdf":
            return self._extract_pdf(content)
        if ext == ".docx":
            return self._extract_docx(content)
        raise UnsupportedDocumentFormatError(
            message=f"Extensión '{ext}' no soportada por el lector documental.",
            context={"extension": ext},
        )

    @staticmethod
    def _extract_pdf(content: bytes) -> ExtractedDocument:
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise UnreadableDocumentError(
                    message="El PDF está protegido con contraseña o cifrado.",
                    context={"encrypted": True},
                )
            pages_text = [page.extract_text() or "" for page in reader.pages]
            return ExtractedDocument(text="\n".join(pages_text), page_count=len(reader.pages))
        except UnreadableDocumentError:
            raise
        except (PyPdfError, Exception) as exc:
            raise CorruptedDocumentError(
                message="El archivo PDF está corrupto o no pudo decodificarse.",
                context={"reason": str(exc)},
            ) from exc

    @staticmethod
    def _extract_docx(content: bytes) -> ExtractedDocument:
        try:
            document = docx.Document(io.BytesIO(content))
            chunks: list[str] = [p.text for p in document.paragraphs if p.text]
            for table in document.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        chunks.append(" | ".join(row_cells))
            return ExtractedDocument(text="\n".join(chunks), page_count=None)
        except Exception as exc:
            raise CorruptedDocumentError(
                message="El archivo DOCX está corrupto o no pudo abrirse.",
                context={"reason": str(exc)},
            ) from exc
