"""Pruebas unitarias de la máquina de estados DefenseState (patrón State)."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.entities.defense_enums import DefenseStateStatus, JuryProfile, Verdict
from app.domain.entities.defense_session import (
    DefenseSession,
    FinalDefenseSummary,
    PlannedQuestion,
)
from app.domain.exceptions.defense_exceptions import InvalidDefenseStateTransitionError


def _sample_session(state: DefenseStateStatus = DefenseStateStatus.PREPARING) -> DefenseSession:
    questions = [
        PlannedQuestion(
            index=i,
            thematic_axis="PROBLEMA",
            question_text=f"Pregunta base {i + 1} sobre el proyecto.",
            evaluation_focus="Dominio conceptual.",
        )
        for i in range(4)
    ]
    return DefenseSession(
        id=uuid4(),
        fdc_document_id=uuid4(),
        jury_profile=JuryProfile.ESTANDAR_UTS,
        state=state,
        current_question_index=0,
        planned_questions=[] if state == DefenseStateStatus.PREPARING else questions,
        custom_vocabulary=[],
        created_at=datetime.now(timezone.utc),
    )


def test_legal_state_transitions_cycle() -> None:
    session = _sample_session(DefenseStateStatus.PREPARING)
    questions = _sample_session(DefenseStateStatus.AURA_SPEAKING).planned_questions

    session.mark_questions_ready(questions, ["TutoIA"])
    assert session.state == DefenseStateStatus.AURA_SPEAKING

    session.mark_speech_delivered()
    assert session.state == DefenseStateStatus.LISTENING_STUDENT

    session.mark_speech_delivered()
    assert session.state == DefenseStateStatus.LISTENING_STUDENT

    session.begin_turn_evaluation()
    assert session.state == DefenseStateStatus.EVALUATING_TURN

    session.advance_to_next_question("Siguiente eje.")
    assert session.state == DefenseStateStatus.AURA_SPEAKING
    assert session.current_question_index == 1

    session.mark_speech_delivered()
    session.begin_turn_evaluation()
    summary = FinalDefenseSummary(
        verdict=Verdict.APROBADO,
        criteria_averages={"pertinencia": 4.0},
        strengths=["Sólido"],
        improvements=["Ninguna mayor"],
        closing_message="Fin.",
        human_in_the_loop_notice="Apoyo al jurado.",
    )
    session.complete(4.0, summary, datetime.now(timezone.utc))
    assert session.state == DefenseStateStatus.COMPLETED


def test_illegal_transitions_raise_invalid_defense_state_transition_error() -> None:
    preparing = _sample_session(DefenseStateStatus.PREPARING)
    with pytest.raises(InvalidDefenseStateTransitionError):
        preparing.begin_turn_evaluation()
    with pytest.raises(InvalidDefenseStateTransitionError):
        preparing.mark_speech_delivered()

    speaking = _sample_session(DefenseStateStatus.AURA_SPEAKING)
    with pytest.raises(InvalidDefenseStateTransitionError):
        speaking.begin_turn_evaluation()
    with pytest.raises(InvalidDefenseStateTransitionError):
        speaking.advance_to_next_question()

    completed = _sample_session(DefenseStateStatus.COMPLETED)
    with pytest.raises(InvalidDefenseStateTransitionError):
        completed.mark_speech_delivered()
    with pytest.raises(InvalidDefenseStateTransitionError):
        completed.begin_turn_evaluation()
