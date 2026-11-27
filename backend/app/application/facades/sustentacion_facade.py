"""Facade de aplicación para los Módulos 2 y 3A (Sustentación Oral y Acta)."""
from uuid import UUID

from app.application.dto.defense_dtos import (
    ActaExportResult,
    CreateDefenseSessionCommand,
    DefenseSessionView,
    SubmitAudioTurnCommand,
    SubmitTextTurnCommand,
    TurnSubmissionResult,
)
from app.application.use_cases.create_defense_session import CreateDefenseSessionUseCase
from app.application.use_cases.export_defense_acta import ExportDefenseActaUseCase
from app.application.use_cases.get_defense_session import GetDefenseSessionUseCase
from app.application.use_cases.submit_defense_turn import SubmitDefenseTurnUseCase
from app.application.use_cases.synthesize_aura_speech import SynthesizeAuraSpeechUseCase
from app.domain.builders.acta_report_data import ActaExportFormat
from app.domain.ports.defense_ai_ports import SynthesizedAudio


class SustentacionFacade:
    """Fachada única de sustentación y actas consumida por defense_router.py."""

    def __init__(
        self,
        create_uc: CreateDefenseSessionUseCase,
        get_uc: GetDefenseSessionUseCase,
        tts_uc: SynthesizeAuraSpeechUseCase,
        submit_turn_uc: SubmitDefenseTurnUseCase,
        export_acta_uc: ExportDefenseActaUseCase,
    ) -> None:
        self._create_uc = create_uc
        self._get_uc = get_uc
        self._tts_uc = tts_uc
        self._submit_turn_uc = submit_turn_uc
        self._export_acta_uc = export_acta_uc

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

    def export_acta(self, session_id: UUID, export_format: ActaExportFormat) -> ActaExportResult:
        return self._export_acta_uc.execute(session_id, export_format)
