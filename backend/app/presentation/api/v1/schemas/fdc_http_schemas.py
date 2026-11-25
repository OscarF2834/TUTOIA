"""Esquemas Pydantic de respuesta HTTP para el Módulo 1 (FDC)."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.application.dto.fdc_ingestion_dto import FdcDocumentView


class AuthorHttpSchema(BaseModel):
    full_name: str
    student_code: str | None = None


class ProjectSummaryHttpSchema(BaseModel):
    title: str
    academic_program: str
    modality: str
    authors: list[AuthorHttpSchema]
    director_name: str | None = None


class AcademicSynthesisHttpSchema(BaseModel):
    central_problem: str
    research_question: str | None = None
    justification_summary: str
    general_objective: str
    specific_objectives: list[str]
    research_type_and_approach: str
    phases_or_stages: list[str]
    technologies_and_instruments: list[str]
    validation_scope: str | None = None
    results_and_conclusions_summary: str | None = None


class CoherenceFindingHttpSchema(BaseModel):
    alignment_axis: str
    status: str
    analysis: str
    document_evidence: str


class DefenseGapHttpSchema(BaseModel):
    thematic_axis: str
    severity: str
    gap_description: str
    suggested_defense_angle: str


class ExecutionMetricsHttpSchema(BaseModel):
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None


class AnalysisDetailHttpSchema(BaseModel):
    strategy_name: str
    model_name: str
    schema_version: str
    overall_coherence_level: str
    academic_synthesis: AcademicSynthesisHttpSchema
    coherence_findings: list[CoherenceFindingHttpSchema]
    detected_gaps: list[DefenseGapHttpSchema]
    execution_metrics: ExecutionMetricsHttpSchema


class ErrorResponseSchema(BaseModel):
    detail: str
    code: str
    context: dict[str, Any]


class FdcDocumentResponseSchema(BaseModel):
    """Contrato unificado de respuesta para POST /upload y GET /{document_id}."""

    document_id: UUID
    project_id: UUID
    analysis_id: UUID
    fdc_type: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    ingestion_status: str
    gemini_file_uri: str | None = None
    created_at: datetime
    project: ProjectSummaryHttpSchema
    analysis: AnalysisDetailHttpSchema

    @classmethod
    def from_view(cls, view: FdcDocumentView) -> "FdcDocumentResponseSchema":
        """Construye el DTO HTTP desde la vista de aplicación."""
        syn = view.analysis.academic_synthesis
        return cls(
            document_id=view.document.id,
            project_id=view.project.id,
            analysis_id=view.analysis.id,
            fdc_type=view.document.fdc_type.value,
            original_filename=view.document.original_filename,
            mime_type=view.document.mime_type,
            file_size_bytes=view.document.file_size_bytes,
            ingestion_status=view.document.ingestion_status.value,
            gemini_file_uri=view.document.gemini_file_uri,
            created_at=view.document.created_at,
            project=ProjectSummaryHttpSchema(
                title=view.project.title,
                academic_program=view.project.academic_program,
                modality=view.project.modality.value,
                authors=[
                    AuthorHttpSchema(full_name=a.full_name, student_code=a.student_code)
                    for a in view.project.authors
                ],
                director_name=view.project.director_name,
            ),
            analysis=AnalysisDetailHttpSchema(
                strategy_name=view.analysis.strategy_name,
                model_name=view.analysis.model_name,
                schema_version=view.analysis.schema_version,
                overall_coherence_level=view.analysis.overall_coherence_level,
                academic_synthesis=AcademicSynthesisHttpSchema(
                    central_problem=syn.central_problem,
                    research_question=syn.research_question,
                    justification_summary=syn.justification_summary,
                    general_objective=syn.general_objective,
                    specific_objectives=syn.specific_objectives,
                    research_type_and_approach=syn.research_type_and_approach,
                    phases_or_stages=syn.phases_or_stages,
                    technologies_and_instruments=syn.technologies_and_instruments,
                    validation_scope=syn.validation_scope,
                    results_and_conclusions_summary=syn.results_and_conclusions_summary,
                ),
                coherence_findings=[
                    CoherenceFindingHttpSchema(
                        alignment_axis=f.alignment_axis,
                        status=f.status,
                        analysis=f.analysis,
                        document_evidence=f.document_evidence,
                    )
                    for f in view.analysis.coherence_findings
                ],
                detected_gaps=[
                    DefenseGapHttpSchema(
                        thematic_axis=g.thematic_axis,
                        severity=g.severity,
                        gap_description=g.gap_description,
                        suggested_defense_angle=g.suggested_defense_angle,
                    )
                    for g in view.analysis.detected_gaps
                ],
                execution_metrics=ExecutionMetricsHttpSchema(
                    latency_ms=view.analysis.execution_metrics.latency_ms,
                    input_tokens=view.analysis.execution_metrics.input_tokens,
                    output_tokens=view.analysis.execution_metrics.output_tokens,
                ),
            ),
        )
