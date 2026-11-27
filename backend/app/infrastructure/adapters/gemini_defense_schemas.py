"""Esquemas Pydantic v2 para Structured Outputs del diálogo de sustentación."""
from typing import Literal

from pydantic import BaseModel, Field


class PlannedQuestionSchema(BaseModel):
    index: int = Field(ge=0, le=3)
    thematic_axis: Literal[
        "PROBLEMA",
        "FUNDAMENTACION",
        "METODOLOGIA_O_PLAN",
        "RESULTADOS_O_VALIDACION",
    ]
    question_text: str = Field(min_length=15)
    evaluation_focus: str = Field(min_length=10)
    source_section: str = Field(
        default="",
        description="Sección exacta del formato FDC consultada, ej. 'Descripción del problema · F-DC-124'.",
    )


class DefenseSessionPlanSchema(BaseModel):
    """Plan de 4 preguntas base y vocabulario técnico del FDC."""

    questions: list[PlannedQuestionSchema] = Field(min_length=4, max_length=4)
    custom_vocabulary: list[str] = Field(
        max_length=50,
        description="Hasta 50 términos técnicos, siglas, autores o conceptos clave del FDC para STT.",
    )


class CriterionScoreSchema(BaseModel):
    code: Literal["pertinencia", "coherencia", "fundamentacion", "metodologia"]
    score: float = Field(ge=0.0, le=5.0)
    rationale: str = Field(min_length=8)


class TurnEvaluationSchema(BaseModel):
    """Evaluación estructurada de una respuesta del sustentante."""

    criterion_scores: list[CriterionScoreSchema] = Field(min_length=4, max_length=4)
    turn_feedback: str = Field(min_length=10)
    strengths: list[str] = Field(min_length=1, max_length=3)
    improvements: list[str] = Field(min_length=1, max_length=3)
    needs_follow_up: bool
    follow_up_question: str | None = None
    transition_message: str = Field(min_length=5)
