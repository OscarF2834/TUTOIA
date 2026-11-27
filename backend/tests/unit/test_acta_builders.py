"""Pruebas unitarias de Builder + Director para Actas Oficiales UTS (PDF y DOCX)."""
import io

import docx

from app.domain.builders.acta_report_data import (
    ActaCriterionRow,
    ActaExportFormat,
    ActaReportData,
    ActaTurnEntry,
)
from app.domain.builders.defense_acta_builder import DefenseActaDirector
from app.infrastructure.builders.acta_builder_factory import ActaBuilderFactory
from app.infrastructure.builders.docx_acta_builder import DocxActaBuilder
from app.infrastructure.builders.pdf_acta_builder import PdfActaBuilder


def _sample_report_data() -> ActaReportData:
    return ActaReportData(
        session_id="12345678-aaaa-bbbb-cccc-1234567890ab",
        generated_at="2026-11-27 16:00 UTC",
        completed_at="2026-11-27 15:58 UTC",
        fdc_type_label="F-DC-125 · Informe Final de Trabajo de Grado",
        project_title="TutoIA: Plataforma inteligente de sustentación académica UTS",
        academic_program="Ingeniería de Sistemas",
        modality_label="Desarrollo Tecnológico",
        director_name="Jaidiver Lombo Guzmán",
        authors=("Pedro Antonio Pérez (1098765432)", "Oscar Javier Gómez (1098765433)"),
        jury_profile_label="Jurado Estándar UTS",
        rubric_name="Rúbrica institucional UTS (2026)",
        overall_score=4.25,
        verdict="APROBADO",
        closing_message="Excelente cierre, Pedro y Oscar. Han concluido su sustentación ante AURA.",
        criteria_rows=(
            ActaCriterionRow("pertinencia", "Pertinencia de la respuesta", 30, 4.50, 1.35),
            ActaCriterionRow("coherencia", "Coherencia y fluidez argumentativa", 25, 4.20, 1.05),
            ActaCriterionRow("fundamentacion", "Fundamentación teórica", 25, 4.00, 1.00),
            ActaCriterionRow("metodologia", "Dominio metodológico", 20, 4.25, 0.85),
        ),
        strengths=("Claridad en la exposición del problema y arquitectura limpia.",),
        improvements=("Precisar métricas adicionales de latencia en carga.",),
        turns=(
            ActaTurnEntry(
                turn_number=1,
                question_index=0,
                is_follow_up=False,
                thematic_axis="PROBLEMA",
                aura_question="Cuéntenme cuál fue el problema central que resolvieron en las UTS.",
                student_transcript="Resolvimos la heterogeneidad al evaluar FDC usando arquitectura limpia.",
                input_mode="AUDIO",
                weighted_score=4.25,
                turn_feedback="Explicación clara y conectada con el informe F-DC-125.",
            ),
        ),
        human_in_the_loop_notice=(
            "Evaluación preliminar generada por AURA como apoyo analítico. "
            "El veredicto académico definitivo corresponde al jurado docente UTS."
        ),
    )


def test_director_with_pdf_builder_generates_valid_pdf_bytes() -> None:
    pdf_bytes = DefenseActaDirector(PdfActaBuilder()).construct(_sample_report_data())
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1024


def test_director_with_docx_builder_generates_complete_editable_docx() -> None:
    docx_bytes = DefenseActaDirector(DocxActaBuilder()).construct(_sample_report_data())
    document = docx.Document(io.BytesIO(docx_bytes))
    all_text = "\n".join(
        [p.text for p in document.paragraphs]
        + [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    )
    assert "TutoIA: Plataforma inteligente de sustentación académica UTS" in all_text
    assert "Pertinencia de la respuesta" in all_text
    assert "Coherencia y fluidez argumentativa" in all_text
    assert "Fundamentación teórica" in all_text
    assert "Dominio metodológico" in all_text
    assert "Resolvimos la heterogeneidad al evaluar FDC usando arquitectura limpia." in all_text
    assert "El veredicto académico definitivo corresponde al jurado docente UTS." in all_text


def test_acta_builder_factory_resolves_pdf_and_docx() -> None:
    factory = ActaBuilderFactory()
    assert isinstance(factory.create(ActaExportFormat.PDF), PdfActaBuilder)
    assert isinstance(factory.create(ActaExportFormat.DOCX), DocxActaBuilder)
