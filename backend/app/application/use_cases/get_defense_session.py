"""Caso de uso: consultar estado e historial de una sesión de sustentación."""
from uuid import UUID

from app.application.dto.defense_dtos import DefenseSessionView
from app.domain.exceptions.defense_exceptions import DefenseSessionNotFoundError
from app.domain.ports.defense_repository_port import DefenseSessionRepositoryPort


class GetDefenseSessionUseCase:
    """Recupera sesión, turnos e interrogante actual para hidratación."""

    def __init__(self, defense_repo: DefenseSessionRepositoryPort) -> None:
        self._defense_repo = defense_repo

    def execute(self, session_id: UUID) -> DefenseSessionView:
        session = self._defense_repo.get_session(session_id)
        if session is None:
            raise DefenseSessionNotFoundError(
                message=f"No existe la sesión de sustentación '{session_id}'.",
                context={"session_id": str(session_id)},
            )
        turns = self._defense_repo.list_turns(session_id)
        return DefenseSessionView(
            session=session,
            turns=turns,
            active_question_text=session.active_prompt_text(turns),
            is_follow_up_pending=session.is_current_prompt_follow_up(turns),
        )
