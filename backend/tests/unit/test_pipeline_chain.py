"""Pruebas unitarias de encadenamiento Chain of Responsibility."""
import pytest

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.core.container import Container
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import InvalidFdcStructureError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from tests.conftest import FDC_124_LINES, FDC_125_LINES, FakeAiAnalyzer, build_pdf


def test_chain_stops_before_gemini_upload_when_structure_fails(
    container: Container,
    fake_analyzer: FakeAiAnalyzer,
) -> None:
    strategy = FdcStrategyFactory.create(FdcType.FDC_125)
    ctx = FdcIngestionContext(
        filename="propuesta.pdf",
        content=build_pdf(FDC_124_LINES),
        strategy=strategy,
    )
    with pytest.raises(InvalidFdcStructureError):
        container.build_pipeline(strategy).handle(ctx)
    assert len(fake_analyzer.upload_calls) == 0


def test_chain_calls_gemini_upload_once_on_valid_fdc_125(
    container: Container,
    fake_analyzer: FakeAiAnalyzer,
) -> None:
    strategy = FdcStrategyFactory.create(FdcType.FDC_125)
    ctx = FdcIngestionContext(
        filename="informe_final.pdf",
        content=build_pdf(FDC_125_LINES),
        strategy=strategy,
    )
    result = container.build_pipeline(strategy).handle(ctx)
    assert result.remote_file is not None
    assert result.remote_file.uri == "https://fake/files/fake123"
    assert len(fake_analyzer.upload_calls) == 1
