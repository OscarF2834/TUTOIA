"""Pruebas unitarias de FdcStructureHandler (FDC-124 vs FDC-125)."""
import pytest

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.fdc_structure_handler import FdcStructureHandler
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import InvalidFdcStructureError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from tests.conftest import FDC_124_LINES


def _ctx(text: str, fdc_type: FdcType) -> FdcIngestionContext:
    return FdcIngestionContext(
        filename="fdc.pdf",
        content=b"",
        strategy=FdcStrategyFactory.create(fdc_type),
        extracted_text=text,
    )


def test_fdc_124_text_passes_with_124_strategy() -> None:
    handler = FdcStructureHandler()
    ctx = handler.handle(_ctx("\n".join(FDC_124_LINES), FdcType.FDC_124))
    assert ctx.extracted_text


def test_fdc_124_text_fails_with_125_strategy_reporting_missing_sections() -> None:
    handler = FdcStructureHandler()
    with pytest.raises(InvalidFdcStructureError) as exc_info:
        handler.handle(_ctx("\n".join(FDC_124_LINES), FdcType.FDC_125))
    assert exc_info.value.code == "FDC_INVALID_STRUCTURE"
    assert exc_info.value.context["missing_sections"] == ["conclusiones", "resultados"]


def test_fdc_124_without_methodology_fails() -> None:
    handler = FdcStructureHandler()
    text = "Planteamiento del problema y Objetivo general del trabajo de grado."
    with pytest.raises(InvalidFdcStructureError) as exc_info:
        handler.handle(_ctx(text, FdcType.FDC_124))
    assert exc_info.value.context["missing_sections"] == ["metodologia"]


def test_accents_and_uppercase_match_normalized_sections() -> None:
    handler = FdcStructureHandler()
    text = "PLANTEAMIENTO DEL PROBLEMA. OBJETIVO GENERAL. METODOLOGÍA DE DESARROLLO."
    ctx = handler.handle(_ctx(text, FdcType.FDC_124))
    assert ctx.extracted_text == text
