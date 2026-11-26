"""Adaptador unificado para extracción preliminar de texto en PDF y DOCX."""
import io

import docx
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
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

    @classmethod
    def _extract_docx(cls, content: bytes) -> ExtractedDocument:
        try:
            document = docx.Document(io.BytesIO(content))
            seen_tcs: set[object] = set()
            chunks = cls._extract_block_items(document.element.body, document, seen_tcs)
            return ExtractedDocument(text="\n".join(chunks), page_count=None)
        except Exception as exc:
            raise CorruptedDocumentError(
                message="El archivo DOCX está corrupto o no pudo abrirse.",
                context={"reason": str(exc)},
            ) from exc

    @classmethod
    def _extract_block_items(cls, container_elm, parent, seen_tcs: set[object]) -> list[str]:
        chunks: list[str] = []
        for child in container_elm.iterchildren():
            if isinstance(child, CT_P):
                text = Paragraph(child, parent).text.strip()
                if text:
                    chunks.append(text)
            elif isinstance(child, CT_Tbl):
                chunks.extend(cls._extract_table_lines(Table(child, parent), seen_tcs))
        return chunks

    @classmethod
    def _extract_table_lines(cls, table: Table, seen_tcs: set[object]) -> list[str]:
        lines: list[str] = []
        for row in table.rows:
            cell_texts = cls._extract_row_cells(row.cells, seen_tcs)
            if len(cell_texts) == 1:
                lines.append(cell_texts[0])
            elif len(cell_texts) > 1:
                lines.append(" | ".join(cell_texts))
        return lines

    @classmethod
    def _extract_row_cells(cls, cells: list[_Cell], seen_tcs: set[object]) -> list[str]:
        cell_texts: list[str] = []
        for cell in cells:
            tc = cell._tc
            if tc in seen_tcs:
                continue
            seen_tcs.add(tc)
            parts = cls._extract_block_items(tc, cell, seen_tcs)
            if parts:
                cell_texts.append("\n".join(parts))
        return cell_texts
