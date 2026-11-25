"""Pruebas unitarias de SizeIntegrityHandler."""
import pytest

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.size_integrity_handler import SizeIntegrityHandler
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import EmptyDocumentError, FileTooLargeError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory


def _make_context(content: bytes) -> FdcIngestionContext:
    return FdcIngestionContext(
        filename="tesis.pdf",
        content=content,
        strategy=FdcStrategyFactory.create(FdcType.FDC_125),
    )


def test_empty_file_raises_empty_document_error() -> None:
    handler = SizeIntegrityHandler(max_bytes=20 * 1024 * 1024)
    with pytest.raises(EmptyDocumentError) as exc_info:
        handler.handle(_make_context(b""))
    assert exc_info.value.code == "FDC_EMPTY_FILE"


def test_oversized_file_raises_file_too_large_error() -> None:
    max_bytes = 20 * 1024 * 1024
    handler = SizeIntegrityHandler(max_bytes=max_bytes)
    with pytest.raises(FileTooLargeError) as exc_info:
        handler.handle(_make_context(b"a" * (max_bytes + 1)))
    assert exc_info.value.code == "FDC_FILE_TOO_LARGE"
    assert exc_info.value.context["max_mb"] == 20


def test_valid_file_populates_size_and_sha256() -> None:
    handler = SizeIntegrityHandler(max_bytes=20 * 1024 * 1024)
    ctx = handler.handle(_make_context(b"%PDF-1.4 contenido"))
    assert ctx.size_bytes == 18
    assert len(ctx.sha256) == 64
