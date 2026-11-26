"""Entidad FdcAnalysis y objetos de valor del análisis documental."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.fdc_document import Modality
from app.domain.entities.project import Author


@dataclass(frozen=True)
class AcademicSynthesis:
    """Síntesis académica estructurada extraída del formato FDC."""

    central_problem: str
    research_question: str | None
    justification_summary: str
    general_objective: str
    specific_objectives: list[str]
    research_type_and_approach: str
    phases_or_stages: list[str]
    technologies_and_instruments: list[str]
    validation_scope: str | None
    results_and_conclusions_summary: str | None


@dataclass(frozen=True)
class CoherenceFinding:
    """Hallazgo de coherencia interna entre ejes del documento."""

    alignment_axis: str
    status: str
    analysis: str
    document_evidence: str


@dataclass(frozen=True)
class DefenseGap:
    """Vacío o punto crítico detectado para guiar preguntas de sustentación."""

    thematic_axis: str
    severity: str
    gap_description: str
    suggested_defense_angle: str


@dataclass(frozen=True)
class ExecutionMetrics:
    """Métricas operativas de ejecución del análisis documental."""

    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_used: str | None = None


@dataclass(frozen=True)
class FdcExtraction:
    """Resultado estructurado producido por el motor de análisis."""

    title: str
    authors: list[Author]
    director_name: str | None
    detected_academic_program: str
    detected_modality: Modality
    synthesis: AcademicSynthesis
    overall_coherence_level: str
    coherence_findings: list[CoherenceFinding]
    detected_gaps: list[DefenseGap]


@dataclass
class FdcAnalysis:
    """Entidad persistible con el diagnóstico completo de un FdcDocument."""

    id: UUID
    fdc_document_id: UUID
    strategy_name: str
    model_name: str
    schema_version: str
    academic_synthesis: AcademicSynthesis
    overall_coherence_level: str
    coherence_findings: list[CoherenceFinding]
    detected_gaps: list[DefenseGap]
    execution_metrics: ExecutionMetrics
    created_at: datetime
