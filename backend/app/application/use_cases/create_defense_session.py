"""Caso de uso: crear sesión de sustentación desde un documento FDC."""
from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.defense_dtos import (
    CreateDefenseSessionCommand,
    DefenseSessionView,
)
from app.application.observers.event_bus import InMemoryEventBus
from app.domain.entities.defense_enums import DefenseStateStatus
from app.domain.entities.defense_session import DefenseSession
from app.domain.events.defense_events import DefenseSessionCreatedEvent
from app.domain.exceptions.fdc_exceptions import FdcDocumentNotFoundError
from app.domain.factories.jury_strategy_factory import JuryStrategyFactory
from app.domain.ports.defense_ai_ports import DefenseAiDialogPort, DefensePreparationInput
from app.domain.ports.defense_repository_port import DefenseSessionRepositoryPort
from app.domain.ports.repositories import (
    FdcAnalysisRepositoryPort,
    FdcDocumentRepositoryPort,
    ProjectRepositoryPort,
    UnitOfWorkPort,
)


class CreateDefenseSessionUseCase:
    """Prepara las 4 preguntas base y crea la sesión de sustentación."""

    def __init__(
        self,
        project_repo: ProjectRepositoryPort,
        document_repo: FdcDocumentRepositoryPort,
        analysis_repo: FdcAnalysisRepositoryPort,
        defense_repo: DefenseSessionRepositoryPort,
        dialog_port: DefenseAiDialogPort,
        uow: UnitOfWorkPort,
        event_bus: InMemoryEventBus,
    ) -> None:
        self._project_repo = project_repo
        self._document_repo = document_repo
        self._analysis_repo = analysis_repo
        self._defense_repo = defense_repo
        self._dialog_port = dialog_port
        self._uow = uow
        self._event_bus = event_bus

    def execute(self, cmd: CreateDefenseSessionCommand) -> DefenseSessionView:
        """Crea la sesión, genera preguntas personalizadas y avanza a AURA_SPEAKING."""
        document = self._document_repo.get(cmd.fdc_document_id)
        if document is None:
            raise FdcDocumentNotFoundError(
                message=f"No existe el documento FDC '{cmd.fdc_document_id}'.",
                context={"document_id": str(cmd.fdc_document_id)},
            )
        project = self._project_repo.get(document.project_id)
        analysis = self._analysis_repo.get_by_document_id(document.id)
        if project is None or analysis is None:
            raise FdcDocumentNotFoundError(
                message=f"El documento FDC '{cmd.fdc_document_id}' no tiene análisis completo.",
                context={"document_id": str(cmd.fdc_document_id)},
            )

        strategy = JuryStrategyFactory.create(cmd.jury_profile)
        now = datetime.now(timezone.utc)
        session = DefenseSession(
            id=uuid4(),
            fdc_document_id=document.id,
            jury_profile=strategy.profile,
            state=DefenseStateStatus.PREPARING,
            current_question_index=0,
            planned_questions=[],
            custom_vocabulary=[],
            created_at=now,
        )

        prep = self._dialog_port.generate_session_plan(
            DefensePreparationInput(
                project=project,
                fdc_type=document.fdc_type,
                analysis=analysis,
                jury_strategy=strategy,
            )
        )
        session.mark_questions_ready(prep.questions, prep.custom_vocabulary)
        self._defense_repo.add_session(session)
        self._uow.commit()

        self._event_bus.publish(
            DefenseSessionCreatedEvent(
                session_id=session.id,
                fdc_document_id=document.id,
                jury_profile=strategy.profile.value,
                occurred_at=now,
            )
        )
        return DefenseSessionView(
            session=session,
            turns=[],
            active_question_text=session.active_prompt_text([]),
            is_follow_up_pending=False,
        )
