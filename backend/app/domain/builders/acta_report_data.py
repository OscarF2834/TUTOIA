"""Modelos de datos inmutables y formatos admitidos para el Acta Oficial de Sustentación."""
from dataclasses import dataclass
from enum import StrEnum


class ActaExportFormat(StrEnum):
    """Formatos de exportación documental soportados por el Módulo 3A."""

    PDF = "pdf"
    DOCX = "docx"


@dataclass(frozen=True)
class ActaCriterionRow:
    """Fila consolidada de un criterio de la rúbrica institucional UTS."""

    code: str
    label: str
    weight_percent: int
    average_score: float
    weighted_contribution: float


@dataclass(frozen=True)
class ActaTurnEntry:
    """Registro de intervención evaluada para incluir en el acta oficial."""

    turn_number: int
    question_index: int
    is_follow_up: bool
    thematic_axis: str
    aura_question: str
    student_transcript: str
    input_mode: str
    weighted_score: float
    turn_feedback: str


@dataclass(frozen=True)
class ActaReportData:
    """Agregado inmutable con toda la información certificable de una sustentación."""

    session_id: str
    generated_at: str
    completed_at: str
    fdc_type_label: str
    project_title: str
    academic_program: str
    modality_label: str
    director_name: str
    authors: tuple[str, ...]
    jury_profile_label: str
    rubric_name: str
    overall_score: float
    verdict: str
    closing_message: str
    criteria_rows: tuple[ActaCriterionRow, ...]
    strengths: tuple[str, ...]
    improvements: tuple[str, ...]
    turns: tuple[ActaTurnEntry, ...]
    human_in_the_loop_notice: str
