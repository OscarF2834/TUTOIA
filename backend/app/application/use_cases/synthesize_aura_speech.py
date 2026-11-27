"""Caso de uso: sintetizar voz humanizada de AURA y actualizar estado."""
from uuid import UUID

from app.domain.entities.defense_enums import DefenseStateStatus
from app.domain.exceptions.defense_exceptions import (
    DefenseSessionNotFoundError,
    InvalidSpeechInputError,
)
from app.domain.ports.defense_ai_ports import SpeechTtsPort, SynthesizedAudio
from app.domain.ports.defense_repository_port import DefenseSessionRepositoryPort
from app.domain.ports.repositories import UnitOfWorkPort


class SynthesizeAuraSpeechUseCase:
    """Genera audio TTS para la pregunta activa o un texto validado de la sesión."""

    def __init__(
        self,
        defense_repo: DefenseSessionRepositoryPort,
        tts_port: SpeechTtsPort,
        uow: UnitOfWorkPort,
    ) -> None:
        self._defense_repo = defense_repo
        self._tts_port = tts_port
        self._uow = uow

    def execute(self, session_id: UUID, text: str | None = None) -> SynthesizedAudio:
        session = self._defense_repo.get_session(session_id)
        if session is None:
            raise DefenseSessionNotFoundError(
                message=f"No existe la sesión de sustentación '{session_id}'.",
                context={"session_id": str(session_id)},
            )
        turns = self._defense_repo.list_turns(session_id)
        clean_requested = text.strip() if text else None

        if clean_requested is None:
            if session.state not in (
                DefenseStateStatus.AURA_SPEAKING,
                DefenseStateStatus.LISTENING_STUDENT,
            ):
                session.mark_speech_delivered()
            target_text = session.active_prompt_text(turns)
            audio = self._tts_port.synthesize(target_text)
            if session.state == DefenseStateStatus.AURA_SPEAKING:
                session.mark_speech_delivered()
                self._defense_repo.update_session(session)
                self._uow.commit()
            return audio

        authorized = session.authorized_tts_texts(turns)
        if clean_requested not in authorized:
            raise InvalidSpeechInputError(
                message="El texto solicitado para TTS no pertenece a los enunciados válidos de esta sesión.",
                context={"session_id": str(session_id)},
            )
        audio = self._tts_port.synthesize(clean_requested)
        if (
            session.state == DefenseStateStatus.AURA_SPEAKING
            and clean_requested == session.active_prompt_text(turns)
        ):
            session.mark_speech_delivered()
            self._defense_repo.update_session(session)
            self._uow.commit()
        return audio
