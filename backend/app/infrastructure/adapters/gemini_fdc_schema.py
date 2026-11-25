"""Esquema Pydantic v2 para Structured Outputs de Gemini sobre formatos FDC."""
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedAuthorSchema(BaseModel):
    full_name: str = Field(description="Nombre completo del estudiante autor del trabajo de grado.")
    student_code: str | None = Field(
        default=None,
        description="Código estudiantil o documento si figura en la portada FDC.",
    )


class ProblemStatementSchema(BaseModel):
    central_problem: str = Field(description="Síntesis clara de la problemática o necesidad abordada.")
    research_question: str | None = Field(
        default=None,
        description="Pregunta de investigación o formulación explícita del problema.",
    )
    justification_summary: str = Field(description="Pertinencia institucional, tecnológica o social del proyecto.")


class ObjectivesSchema(BaseModel):
    general_objective: str = Field(description="Objetivo general textual o fielmente sintetizado del documento FDC.")
    specific_objectives: list[str] = Field(
        min_length=1,
        description="Lista ordenada de objetivos específicos del proyecto.",
    )


class MethodologySchema(BaseModel):
    research_type_and_approach: str = Field(description="Tipo de investigación, enfoque y diseño metodológico declarado.")
    phases_or_stages: list[str] = Field(description="Fases metodológicas ejecutadas o propuestas.")
    technologies_and_instruments: list[str] = Field(
        description="Herramientas, frameworks, técnicas o instrumentos de recolección/validación.",
    )
    validation_scope: str | None = Field(
        default=None,
        description="Población, muestra, dataset o escenario de pruebas empleado.",
    )


class CoherenceFindingSchema(BaseModel):
    alignment_axis: Literal[
        "PROBLEMA_OBJETIVOS",
        "OBJETIVOS_METODOLOGIA",
        "METODOLOGIA_RESULTADOS",
        "MARCO_TEORICO_REFERENTES",
    ]
    status: Literal["SOLIDO", "PARCIAL", "DEFICIENTE"]
    analysis: str = Field(description="Evaluación objetiva de coherencia interna en este eje.")
    document_evidence: str = Field(description="Sección o hallazgo concreto del documento que sustenta la observación.")


class DefenseGapSchema(BaseModel):
    thematic_axis: Literal["CONTEXTO", "PROBLEMA", "FUNDAMENTACION", "METODOLOGIA", "RESULTADOS", "CONCLUSIONES"]
    severity: Literal["ALTA", "MEDIA", "BAJA"]
    gap_description: str = Field(description="Vacío argumental, ambigüedad técnica o falta de evidencia detectada en el FDC.")
    suggested_defense_angle: str = Field(
        description="Ángulo concreto sobre el cual AURA deberá indagar al estudiante durante la sustentación.",
    )


class FdcGeminiExtractionSchema(BaseModel):
    """Contrato estricto de salida estructurada extraída por Gemini."""

    title: str = Field(description="Título completo del proyecto de grado.")
    authors: list[ExtractedAuthorSchema] = Field(min_length=1)
    director_name: str | None = Field(default=None)
    detected_academic_program: str = Field(description="Programa académico UTS identificado en el formato FDC.")
    detected_modality: Literal["DESARROLLO_TECNOLOGICO", "INVESTIGACION", "MONOGRAFIA", "EMPRENDIMIENTO"]
    problem: ProblemStatementSchema
    objectives: ObjectivesSchema
    methodology: MethodologySchema
    results_and_conclusions_summary: str | None = Field(
        default=None,
        description="Síntesis de resultados alcanzados, productos y conclusiones (obligatorio en FDC-125; opcional en FDC-124).",
    )
    overall_coherence_level: Literal["ALTA", "MEDIA", "BAJA"]
    coherence_findings: list[CoherenceFindingSchema] = Field(min_length=2)
    detected_gaps_for_defense: list[DefenseGapSchema] = Field(
        min_length=3,
        max_length=6,
        description="Entre 3 y 6 vacíos o puntos críticos verificables que alimentarán el generador de preguntas de sustentación.",
    )
