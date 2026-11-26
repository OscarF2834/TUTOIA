"""Pruebas unitarias de TextReadabilityHandler y DocumentReaderAdapter."""
import io

import docx
import pytest

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.text_readability_handler import TextReadabilityHandler
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import CorruptedDocumentError, UnreadableDocumentError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from app.infrastructure.adapters.document_reader_adapter import DocumentReaderAdapter
from tests.conftest import FDC_124_LINES, build_pdf


def _ctx(content: bytes, ext: str = ".pdf") -> FdcIngestionContext:
    return FdcIngestionContext(
        filename=f"doc{ext}",
        content=content,
        strategy=FdcStrategyFactory.create(FdcType.FDC_124),
        extension=ext,
    )


def test_build_pdf_helper_text_is_extracted_by_pypdf() -> None:
    reader = DocumentReaderAdapter()
    pdf_bytes = build_pdf(FDC_124_LINES)
    extracted = reader.extract(pdf_bytes, ".pdf")
    assert "Planteamiento del problema" in extracted.text
    assert extracted.page_count == 1


def test_docx_reader_deduplicates_merged_cells_and_reads_nested_tables() -> None:
    document = docx.Document()
    table = document.add_table(rows=2, cols=4)
    merged_cell = table.rows[0].cells[0].merge(table.rows[0].cells[3])
    merged_cell.text = "CONTENIDO DE CELDA COMBINADA UTS"

    host_cell = table.rows[1].cells[0]
    host_cell.text = "Plan de actividades"
    nested = host_cell.add_table(rows=1, cols=2)
    nested.rows[0].cells[0].text = "Fase 1"
    nested.rows[0].cells[1].text = "Diseno limpio"

    buf = io.BytesIO()
    document.save(buf)

    extracted = DocumentReaderAdapter().extract(buf.getvalue(), ".docx")
    assert extracted.text.count("CONTENIDO DE CELDA COMBINADA UTS") == 1
    assert "Plan de actividades" in extracted.text
    assert "Fase 1 | Diseno limpio" in extracted.text


def test_blank_pdf_raises_unreadable() -> None:
    handler = TextReadabilityHandler(reader=DocumentReaderAdapter(), min_chars=500)
    with pytest.raises(UnreadableDocumentError) as exc_info:
        handler.handle(_ctx(build_pdf([])))
    assert exc_info.value.code == "FDC_UNREADABLE"


def test_short_text_pdf_raises_unreadable() -> None:
    handler = TextReadabilityHandler(reader=DocumentReaderAdapter(), min_chars=500)
    with pytest.raises(UnreadableDocumentError):
        handler.handle(_ctx(build_pdf(["Texto muy corto"])))


def test_corrupted_pdf_raises_corrupted_document_error() -> None:
    handler = TextReadabilityHandler(reader=DocumentReaderAdapter(), min_chars=500)
    with pytest.raises(CorruptedDocumentError) as exc_info:
        handler.handle(_ctx(b"%PDF-garbage"))
    assert exc_info.value.code == "FDC_CORRUPTED_FILE"
