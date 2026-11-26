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


def test_fdc_124_without_methodology_or_plan_fails() -> None:
    handler = FdcStructureHandler()
    text = "Descripcion del problema, Justificacion y Objetivo general del trabajo de grado."
    with pytest.raises(InvalidFdcStructureError) as exc_info:
        handler.handle(_ctx(text, FdcType.FDC_124))
    assert exc_info.value.context["missing_sections"] == ["plan_o_metodologia"]


def test_accents_and_uppercase_match_normalized_sections() -> None:
    handler = FdcStructureHandler()
    text = (
        "DESCRIPCIÓN DEL PROBLEMA. JUSTIFICACIÓN. OBJETIVO GENERAL. "
        "PLAN DE ACTIVIDADES Y METODOLOGÍA DE DESARROLLO."
    )
    ctx = handler.handle(_ctx(text, FdcType.FDC_124))
    assert ctx.extracted_text == text


def test_realistic_uts_fdc_124_without_methodology_word_passes() -> None:
    handler = FdcStructureHandler()
    realistic_uts_fdc_124 = (
        "Ficha tecnica de la propuesta. "
        "Descripcion del problema: se requiere optimizar la gestion academica de proyectos de grado. "
        "Justificacion: mejora la trazabilidad documental en la FCNI. "
        "Objetivo General: construir una plataforma web de apoyo academico. "
        "Objetivos especificos: analizar requerimientos y validar el prototipo. "
        "Estado del arte y Fundamento Teorico: revision de modelos de lenguaje aplicados a educacion. "
        "Resultados esperados: aplicacion funcional y reporte de validacion. "
        "Plan de actividades: fase 1 analisis, fase 2 diseno, fase 3 pruebas."
    )
    assert "metodolog" not in realistic_uts_fdc_124.lower()
    ctx = handler.handle(_ctx(realistic_uts_fdc_124, FdcType.FDC_124))
    assert ctx.extracted_text == realistic_uts_fdc_124


def test_realistic_uts_fdc_125_with_diseno_and_desarrollo_without_methodology_word_passes() -> None:
    handler = FdcStructureHandler()
    realistic_uts_fdc_125 = (
        "Resumen Ejecutivo: plataforma TutoIA para sustentaciones UTS. "
        "Planteamiento del problema: variabilidad al evaluar defensas de grado. "
        "Objetivo General: desarrollar la plataforma web inteligente. "
        "Diseño de la Investigación: enfoque computacional en cuatro etapas. "
        "Desarrollo del Trabajo de Grado: implementacion modular del sistema. "
        "Resultados: pruebas funcionales exitosas con 94 por ciento de precision. "
        "Conclusiones: el soporte analitico estandariza la evaluacion docente."
    )
    assert "metodolog" not in realistic_uts_fdc_125.lower()
    ctx = handler.handle(_ctx(realistic_uts_fdc_125, FdcType.FDC_125))
    assert ctx.extracted_text == realistic_uts_fdc_125


def test_fdc_125_without_design_or_methodology_fails() -> None:
    handler = FdcStructureHandler()
    text = (
        "Planteamiento del problema. Objetivo general. "
        "Resultados obtenidos en las pruebas. Conclusiones finales."
    )
    with pytest.raises(InvalidFdcStructureError) as exc_info:
        handler.handle(_ctx(text, FdcType.FDC_125))
    assert exc_info.value.context["missing_sections"] == ["diseno_o_metodologia"]
