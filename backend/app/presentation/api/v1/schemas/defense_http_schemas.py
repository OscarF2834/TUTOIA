"""Esquemas Pydantic HTTP v1 para el Módulo 2 (Sustentación Oral)."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.defense_dtos import DefenseSessionView, TurnSubmissionResult
from app.domain.entities.defense_session import DefenseTurn, FinalDefenseSummary


class CreateDefenseSessionRequestSchema(BaseModel):
    fdc_document_id: UUID
    jury_profile: Literal["ESTANDAR_UTS", "TECNICO_RIGUROSO"] = "ESTANDAR_UTS"


class TtsSynthesizeRequestSchema(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=3000)


class SubmitTextTurnRequestSchema(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class PlannedQuestionHttpSchema(BaseModel):
    index: int
    thematic_axis: str
    question_text: str
    evaluation_focus: str


class CriterionScoreHttpSchema(BaseModel):
    code: str
    label: str
    weight: float
    score: float
    rationale: str


class DefenseTurnHttpSchema(BaseModel):
    id: UUID
    turn_number: int
    question_index: int
    is_follow_up: bool
    thematic_axis: str
    aura_question_text: str
    student_transcript: str
    input_mode: str
    weighted_score: float
    criteria: list[CriterionScoreHttpSchema]
    turn_feedback: str
    needs_follow_up: bool
    latency_ms: int
    created_at: datetime

    @classmethod
    def from_domain(cls, turn: DefenseTurn) -> "DefenseTurnHttpSchema":
        return cls(
            id=turn.id,
            turn_number=turn.turn_number,
            question_index=turn.question_index,
            is_follow_up=turn.is_follow_up,
            thematic_axis=turn.thematic_axis,
            aura_question_text=turn.aura_question_text,
            student_transcript=turn.student_transcript,
            input_mode=turn.input_mode.value,
            weighted_score=turn.rubric_scores.weighted_score,
            criteria=[
                CriterionScoreHttpSchema(
                    code=c.code,
                    label=c.label,
                    weight=c.weight,
                    score=c.score,
                    rationale=c.rationale,
                )
                for c in turn.rubric_scores.criteria
            ],
            turn_feedback=turn.turn_feedback,
            needs_follow_up=turn.needs_follow_up,
            latency_ms=turn.latency_ms,
            created_at=turn.created_at,
        )


class FinalDefenseSummaryHttpSchema(BaseModel):
    verdict: str
    criteria_averages: dict[str, float]
    strengths: list[str]
    improvements: list[str]
    closing_message: str
    human_in_the_loop_notice: str

    @classmethod
    def from_domain(cls, summary: FinalDefenseSummary) -> "FinalDefenseSummaryHttpSchema":
        return cls(
            verdict=summary.verdict.value,
            criteria_averages=summary.criteria_averages,
            strengths=summary.strengths,
            improvements=summary.improvements,
            closing_message=summary.closing_message,
            human_in_the_loop_notice=summary.human_in_the_loop_notice,
        )


class DefenseSessionResponseSchema(BaseModel):
    session_id: UUID
    fdc_document_id: UUID
    jury_profile: str
    state: str
    current_question_index: int
    total_questions: int
    active_question_text: str
    is_follow_up_pending: bool
    planned_questions: list[PlannedQuestionHttpSchema]
    custom_vocabulary: list[str]
    turns: list[DefenseTurnHttpSchema]
    overall_score: float | None = None
    final_summary: FinalDefenseSummaryHttpSchema | None = None
    created_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def from_view(cls, view: DefenseSessionView) -> "DefenseSessionResponseSchema":
        s = view.session
        return cls(
            session_id=s.id,
            fdc_document_id=s.fdc_document_id,
            jury_profile=s.jury_profile.value,
            state=s.state.value,
            current_question_index=s.current_question_index,
            total_questions=len(s.planned_questions),
            active_question_text=view.active_question_text,
            is_follow_up_pending=view.is_follow_up_pending,
            planned_questions=[
                PlannedQuestionHttpSchema(
                    index=q.index,
                    thematic_axis=q.thematic_axis,
                    question_text=q.question_text,
                    evaluation_focus=q.evaluation_focus,
                )
                for q in s.planned_questions
            ],
            custom_vocabulary=s.custom_vocabulary,
            turns=[DefenseTurnHttpSchema.from_domain(t) for t in view.turns],
            overall_score=s.overall_score,
            final_summary=FinalDefenseSummaryHttpSchema.from_domain(s.final_summary)
            if s.final_summary
            else None,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )


class TurnSubmissionResponseSchema(BaseModel):
    session_id: UUID
    state: str
    current_question_index: int
    evaluated_turn: DefenseTurnHttpSchema
    next_question_text: str | None = None
    is_follow_up_pending: bool
    is_completed: bool
    overall_score: float | None = None
    final_summary: FinalDefenseSummaryHttpSchema | None = None

    @classmethod
    def from_result(cls, res: TurnSubmissionResult) -> "TurnSubmissionResponseSchema":
        s = res.session
        return cls(
            session_id=s.id,
            state=s.state.value,
            current_question_index=s.current_question_index,
            evaluated_turn=DefenseTurnHttpSchema.from_domain(res.evaluated_turn),
            next_question_text=res.next_question_text,
            is_follow_up_pending=res.is_follow_up_pending,
            is_completed=res.is_completed,
            overall_score=s.overall_score,
            final_summary=FinalDefenseSummaryHttpSchema.from_domain(s.final_summary)
            if s.final_summary
            else None,
        )
