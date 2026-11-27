"""Repositorio SQLAlchemy 2.0 para sesiones y turnos de sustentación."""
from dataclasses import asdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.defense_enums import (
    DefenseStateStatus,
    InputMode,
    JuryProfile,
    Verdict,
)
from app.domain.entities.defense_session import (
    CriterionScoreDetail,
    DefenseSession,
    DefenseTurn,
    FinalDefenseSummary,
    PlannedQuestion,
    TurnRubricEvaluation,
)
from app.infrastructure.db.models.defense_session_model import DefenseSessionModel
from app.infrastructure.db.models.defense_turn_model import DefenseTurnModel


class SqlAlchemyDefenseRepository:
    """Implementa DefenseSessionRepositoryPort sobre SQLAlchemy 2.0."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_session(self, defense_session: DefenseSession) -> None:
        summary_dict = asdict(defense_session.final_summary) if defense_session.final_summary else None
        model = DefenseSessionModel(
            id=defense_session.id,
            fdc_document_id=defense_session.fdc_document_id,
            jury_profile=defense_session.jury_profile.value,
            state=defense_session.state.value,
            current_question_index=defense_session.current_question_index,
            planned_questions=[asdict(q) for q in defense_session.planned_questions],
            custom_vocabulary=list(defense_session.custom_vocabulary),
            overall_score=defense_session.overall_score,
            final_summary=summary_dict,
            created_at=defense_session.created_at,
            completed_at=defense_session.completed_at,
        )
        self._session.add(model)

    def update_session(self, defense_session: DefenseSession) -> None:
        model = self._session.get(DefenseSessionModel, defense_session.id)
        if model is None:
            return
        model.state = defense_session.state.value
        model.current_question_index = defense_session.current_question_index
        model.planned_questions = [asdict(q) for q in defense_session.planned_questions]
        model.custom_vocabulary = list(defense_session.custom_vocabulary)
        model.overall_score = defense_session.overall_score
        model.final_summary = (
            asdict(defense_session.final_summary) if defense_session.final_summary else None
        )
        model.completed_at = defense_session.completed_at

    def get_session(self, session_id: UUID) -> DefenseSession | None:
        model = self._session.get(DefenseSessionModel, session_id)
        if model is None:
            return None
        summary = self._map_summary(model.final_summary) if model.final_summary else None
        return DefenseSession(
            id=model.id,
            fdc_document_id=model.fdc_document_id,
            jury_profile=JuryProfile(model.jury_profile),
            state=DefenseStateStatus(model.state),
            current_question_index=model.current_question_index,
            planned_questions=[PlannedQuestion(**q) for q in model.planned_questions],
            custom_vocabulary=list(model.custom_vocabulary),
            overall_score=model.overall_score,
            final_summary=summary,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    def add_turn(self, turn: DefenseTurn) -> None:
        model = DefenseTurnModel(
            id=turn.id,
            session_id=turn.session_id,
            turn_number=turn.turn_number,
            question_index=turn.question_index,
            is_follow_up=turn.is_follow_up,
            thematic_axis=turn.thematic_axis,
            aura_question_text=turn.aura_question_text,
            student_transcript=turn.student_transcript,
            input_mode=turn.input_mode.value,
            rubric_scores=asdict(turn.rubric_scores),
            turn_feedback=turn.turn_feedback,
            needs_follow_up=turn.needs_follow_up,
            latency_ms=turn.latency_ms,
            created_at=turn.created_at,
        )
        self._session.add(model)

    def list_turns(self, session_id: UUID) -> list[DefenseTurn]:
        models = (
            self._session.query(DefenseTurnModel)
            .filter(DefenseTurnModel.session_id == session_id)
            .order_by(DefenseTurnModel.turn_number.asc())
            .all()
        )
        return [self._map_turn(m) for m in models]

    @staticmethod
    def _map_summary(data: dict) -> FinalDefenseSummary:
        return FinalDefenseSummary(
            verdict=Verdict(data["verdict"]),
            criteria_averages=dict(data["criteria_averages"]),
            strengths=list(data["strengths"]),
            improvements=list(data["improvements"]),
            closing_message=data["closing_message"],
            human_in_the_loop_notice=data["human_in_the_loop_notice"],
        )

    @staticmethod
    def _map_turn(model: DefenseTurnModel) -> DefenseTurn:
        rubric_data = model.rubric_scores
        evaluation = TurnRubricEvaluation(
            weighted_score=float(rubric_data["weighted_score"]),
            criteria=[CriterionScoreDetail(**c) for c in rubric_data["criteria"]],
        )
        return DefenseTurn(
            id=model.id,
            session_id=model.session_id,
            turn_number=model.turn_number,
            question_index=model.question_index,
            is_follow_up=model.is_follow_up,
            thematic_axis=model.thematic_axis,
            aura_question_text=model.aura_question_text,
            student_transcript=model.student_transcript,
            input_mode=InputMode(model.input_mode),
            rubric_scores=evaluation,
            turn_feedback=model.turn_feedback,
            needs_follow_up=model.needs_follow_up,
            latency_ms=model.latency_ms,
            created_at=model.created_at,
        )
