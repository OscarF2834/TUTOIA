"""Patrón State para la máquina de estados de sustentación."""
from abc import ABC
from typing import TYPE_CHECKING

from app.domain.entities.defense_enums import DefenseStateStatus
from app.domain.exceptions.defense_exceptions import InvalidDefenseStateTransitionError

if TYPE_CHECKING:
    from app.domain.entities.defense_session import DefenseSession


class DefenseState(ABC):
    """Estado abstracto de una sesión de sustentación oral."""

    status: DefenseStateStatus

    def on_questions_ready(self, session: "DefenseSession") -> None:
        self._reject("cargar preguntas iniciales")

    def on_speech_delivered(self, session: "DefenseSession") -> None:
        self._reject("locutar o habilitar micrófono")

    def on_begin_evaluation(self, session: "DefenseSession") -> None:
        self._reject("enviar respuesta para evaluación")

    def on_turn_evaluated_continue(self, session: "DefenseSession") -> None:
        self._reject("continuar hacia la siguiente pregunta")

    def on_turn_evaluated_complete(self, session: "DefenseSession") -> None:
        self._reject("finalizar la sesión de sustentación")

    def _reject(self, action: str) -> None:
        raise InvalidDefenseStateTransitionError(
            message=f"No se permite '{action}' mientras la sesión está en estado {self.status.value}.",
            context={"current_state": self.status.value, "attempted_action": action},
        )


class PreparingState(DefenseState):
    """Sesión recién creada preparando preguntas base."""

    status = DefenseStateStatus.PREPARING

    def on_questions_ready(self, session: "DefenseSession") -> None:
        session.state = DefenseStateStatus.AURA_SPEAKING


class AuraSpeakingState(DefenseState):
    """AURA tiene una pregunta o contrapregunta lista para ser locutada."""

    status = DefenseStateStatus.AURA_SPEAKING

    def on_speech_delivered(self, session: "DefenseSession") -> None:
        session.state = DefenseStateStatus.LISTENING_STUDENT


class ListeningStudentState(DefenseState):
    """Sistema escuchando o esperando la respuesta del estudiante."""

    status = DefenseStateStatus.LISTENING_STUDENT

    def on_speech_delivered(self, session: "DefenseSession") -> None:
        session.state = DefenseStateStatus.LISTENING_STUDENT

    def on_begin_evaluation(self, session: "DefenseSession") -> None:
        session.state = DefenseStateStatus.EVALUATING_TURN


class EvaluatingTurnState(DefenseState):
    """Evaluación del turno actual en curso."""

    status = DefenseStateStatus.EVALUATING_TURN

    def on_turn_evaluated_continue(self, session: "DefenseSession") -> None:
        session.state = DefenseStateStatus.AURA_SPEAKING

    def on_turn_evaluated_complete(self, session: "DefenseSession") -> None:
        session.state = DefenseStateStatus.COMPLETED


class CompletedState(DefenseState):
    """Estado terminal de la sustentación; no admite nuevas acciones."""

    status = DefenseStateStatus.COMPLETED


_STATE_REGISTRY: dict[DefenseStateStatus, DefenseState] = {
    DefenseStateStatus.PREPARING: PreparingState(),
    DefenseStateStatus.AURA_SPEAKING: AuraSpeakingState(),
    DefenseStateStatus.LISTENING_STUDENT: ListeningStudentState(),
    DefenseStateStatus.EVALUATING_TURN: EvaluatingTurnState(),
    DefenseStateStatus.COMPLETED: CompletedState(),
}


def resolve_defense_state(status: DefenseStateStatus) -> DefenseState:
    """Resuelve la instancia concreta del patrón State."""
    return _STATE_REGISTRY[status]
