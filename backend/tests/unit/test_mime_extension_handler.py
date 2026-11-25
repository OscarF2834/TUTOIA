"""Pruebas unitarias de MimeExtensionHandler."""
import io
import zipfile

import pytest

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.mime_extension_handler import (
    DOCX_MIME,
    PDF_MIME,
    MimeExtensionHandler,
)
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import UnsupportedDocumentFormatError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from tests.conftest import FDC_124_LINES, build_docx, build_pdf


def _ctx(filename: str, content: bytes) -> FdcIngestionContext:
    return FdcIngestionContext(
        filename=filename,
        content=content,
        strategy=FdcStrategyFactory.create(FdcType.FDC_124),
    )


def test_txt_extension_rejected() -> None:
    handler = MimeExtensionHandler()
    with pytest.raises(UnsupportedDocumentFormatError):
        handler.handle(_ctx("notas.txt", b"texto plano"))


def test_pdf_extension_with_zip_magic_rejected() -> None:
    handler = MimeExtensionHandler()
    with pytest.raises(UnsupportedDocumentFormatError):
        handler.handle(_ctx("falso.pdf", b"PK\x03\x04zipbytes"))


def test_pdf_extension_with_plain_bytes_rejected() -> None:
    handler = MimeExtensionHandler()
    with pytest.raises(UnsupportedDocumentFormatError):
        handler.handle(_ctx("falso.pdf", b"hello world"))


def test_docx_zip_without_document_xml_rejected() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("other/file.xml", "<root/>")
    handler = MimeExtensionHandler()
    with pytest.raises(UnsupportedDocumentFormatError):
        handler.handle(_ctx("invalido.docx", buf.getvalue()))


def test_valid_pdf_sets_pdf_mime() -> None:
    handler = MimeExtensionHandler()
    ctx = handler.handle(_ctx("propuesta.PDF", build_pdf(FDC_124_LINES)))
    assert ctx.extension == ".pdf"
    assert ctx.mime_type == PDF_MIME


def test_valid_docx_sets_docx_mime() -> None:
    handler = MimeExtensionHandler()
    ctx = handler.handle(_ctx("propuesta.docx", build_docx(FDC_124_LINES)))
    assert ctx.extension == ".docx"
    assert ctx.mime_type == DOCX_MIME
