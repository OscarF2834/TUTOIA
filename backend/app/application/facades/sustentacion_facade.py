"""Facade de aplicación para el Módulo 2 (Sustentación Oral con AURA)."""
from uuid import UUID

from app.application.dto.defense_dtos import (
    CreateDefenseSessionCommand,
    DefenseSessionView,
    SubmitAudioTurnCommand,
    SubmitTextTurnCommand,
    TurnSubmissionResult,
)
from app.application.use_cases.create_defense_session import CreateDefenseSessionUseCase
from app.application.use_cases.get_defense_session import GetDefenseSessionUseCase
from app.application.use_cases.submit_defense_turn import SubmitDefenseTurnUseCase
from app.application.use_cases.synthesize_aura_speech import SynthesizeAuraSpeechUseCase
from app.domain.ports.defense_ai_ports import SynthesizedAudio


class SustentacionFacade:
    """Fachada única del Módulo 2 consumida por defense_router.py."""

    def __init__(
        self,
        create_uc: CreateDefenseSessionUseCase,
        get_uc: GetDefenseSessionUseCase,
        tts_uc: SynthesizeAuraSpeechUseCase,
        submit_turn_uc: SubmitDefenseTurnUseCase,
    ) -> None:
        self._create_uc = create_uc
        self._get_uc = get_uc
        self._tts_uc = tts_uc
        self._submit_turn_uc = submit_turn_uc

    def create_session(self, cmd: CreateDefenseSessionCommand) -> DefenseSessionView:
        return self._create_uc.execute(cmd)

    def get_session(self, session_id: UUID) -> DefenseSessionView:
        return self._get_uc.execute(session_id)

    def synthesize_speech(self, session_id: UUID, text: str | None = None) -> SynthesizedAudio:
        return self._tts_uc.execute(session_id, text=text)

    def submit_audio_turn(self, cmd: SubmitAudioTurnCommand) -> TurnSubmissionResult:
        return self._submit_turn_uc.execute_audio(cmd)

    def submit_text_turn(self, cmd: SubmitTextTurnCommand) -> TurnSubmissionResult:
        return self._submit_turn_uc.execute_text(cmd)
