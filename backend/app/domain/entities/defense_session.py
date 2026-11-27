"""Entidades DefenseSession, DefenseTurn y agregados de sustentación."""
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from app.domain.entities.defense_enums import (
    DefenseStateStatus,
    InputMode,
    JuryProfile,
    Verdict,
)
from app.domain.states.defense_state import resolve_defense_state


@dataclass(frozen=True)
class PlannedQuestion:
    """Pregunta base planeada para la sustentación (y posible contrapregunta activa)."""

    index: int
    thematic_axis: str
    question_text: str
    evaluation_focus: str
    pending_follow_up_text: str | None = None
    transition_message: str | None = None
    source_section: str = ""


@dataclass(frozen=True)
class CriterionScoreDetail:
    """Puntaje y justificación individual de un criterio de la rúbrica."""

    code: str
    label: str
    weight: float
    score: float
    rationale: str


@dataclass(frozen=True)
class TurnRubricEvaluation:
    """Evaluación ponderada de un turno contra la rúbrica UTS."""

    weighted_score: float
    criteria: list[CriterionScoreDetail]


@dataclass(frozen=True)
class DefenseTurn:
    """Registro inmutable de una interacción pregunta ↔ respuesta evaluada."""

    id: UUID
    session_id: UUID
    turn_number: int
    question_index: int
    is_follow_up: bool
    thematic_axis: str
    aura_question_text: str
    student_transcript: str
    input_mode: InputMode
    rubric_scores: TurnRubricEvaluation
    turn_feedback: str
    needs_follow_up: bool
    latency_ms: int
    created_at: datetime


@dataclass(frozen=True)
class FinalDefenseSummary:
    """Resumen consolidado al concluir los ejes de sustentación."""

    verdict: Verdict
    criteria_averages: dict[str, float]
    strengths: list[str]
    improvements: list[str]
    closing_message: str
    human_in_the_loop_notice: str


@dataclass
class DefenseSession:
    """Entidad raíz de una sesión de sustentación oral conducida por AURA."""

    id: UUID
    fdc_document_id: UUID
    jury_profile: JuryProfile
    state: DefenseStateStatus
    current_question_index: int
    planned_questions: list[PlannedQuestion]
    custom_vocabulary: list[str]
    created_at: datetime
    overall_score: float | None = None
    final_summary: FinalDefenseSummary | None = None
    completed_at: datetime | None = None

    def mark_questions_ready(self, questions: list[PlannedQuestion], vocabulary: list[str]) -> None:
        resolve_defense_state(self.state).on_questions_ready(self)
        self.planned_questions = questions
        self.custom_vocabulary = vocabulary[:50]

    def mark_speech_delivered(self) -> None:
        resolve_defense_state(self.state).on_speech_delivered(self)

    def begin_turn_evaluation(self) -> None:
        resolve_defense_state(self.state).on_begin_evaluation(self)

    def advance_with_follow_up(self, follow_up_text: str) -> None:
        resolve_defense_state(self.state).on_turn_evaluated_continue(self)
        current = self.planned_questions[self.current_question_index]
        self.planned_questions[self.current_question_index] = replace(
            current,
            pending_follow_up_text=follow_up_text,
        )

    def advance_to_next_question(self, transition_message: str | None = None) -> None:
        resolve_defense_state(self.state).on_turn_evaluated_continue(self)
        current = self.planned_questions[self.current_question_index]
        self.planned_questions[self.current_question_index] = replace(
            current,
            pending_follow_up_text=None,
        )
        self.current_question_index += 1
        clean_transition = (transition_message or "").strip() or None
        if clean_transition and self.current_question_index < len(self.planned_questions):
            next_q = self.planned_questions[self.current_question_index]
            self.planned_questions[self.current_question_index] = replace(
                next_q,
                transition_message=clean_transition,
            )

    def complete(self, overall_score: float, summary: FinalDefenseSummary, completed_at: datetime) -> None:
        resolve_defense_state(self.state).on_turn_evaluated_complete(self)
        current = self.planned_questions[self.current_question_index]
        self.planned_questions[self.current_question_index] = replace(current, pending_follow_up_text=None)
        self.overall_score = overall_score
        self.final_summary = summary
        self.completed_at = completed_at

    def current_question(self) -> PlannedQuestion:
        return self.planned_questions[self.current_question_index]

    def has_follow_up_for_current_question(self, turns: list[DefenseTurn]) -> bool:
        return any(
            t.question_index == self.current_question_index and t.is_follow_up
            for t in turns
        )

    def is_current_prompt_follow_up(self, turns: list[DefenseTurn]) -> bool:
        current = self.current_question()
        return bool(current.pending_follow_up_text) and not self.has_follow_up_for_current_question(turns)

    def active_prompt_text(self, turns: list[DefenseTurn]) -> str:
        if self.state == DefenseStateStatus.COMPLETED and self.final_summary:
            return self.final_summary.closing_message
        current = self.current_question()
        if self.is_current_prompt_follow_up(turns) and current.pending_follow_up_text:
            return current.pending_follow_up_text
        if current.transition_message and current.transition_message.strip():
            transition = current.transition_message.strip()
            question = current.question_text.strip()
            if question.lower() in transition.lower():
                return transition
            return f"{transition} {question}"
        return current.question_text

    def authorized_tts_texts(self, turns: list[DefenseTurn]) -> set[str]:
        texts: set[str] = {self.active_prompt_text(turns)}
        for q in self.planned_questions:
            texts.add(q.question_text)
            if q.transition_message and q.transition_message.strip():
                texts.add(f"{q.transition_message.strip()} {q.question_text.strip()}")
            if q.pending_follow_up_text:
                texts.add(q.pending_follow_up_text)
        for t in turns:
            texts.add(t.aura_question_text)
            if t.turn_feedback:
                texts.add(t.turn_feedback)
        if self.final_summary:
            texts.add(self.final_summary.closing_message)
        return texts
