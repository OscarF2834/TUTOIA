"""DTOs de aplicación para el Módulo 2 (sustentación oral)."""
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.defense_enums import JuryProfile
from app.domain.entities.defense_session import DefenseSession, DefenseTurn


@dataclass(frozen=True)
class CreateDefenseSessionCommand:
    """Comando para inicializar una sustentación desde un documento FDC."""

    fdc_document_id: UUID
    jury_profile: JuryProfile = JuryProfile.ESTANDAR_UTS


@dataclass(frozen=True)
class SubmitAudioTurnCommand:
    """Comando para evaluar una respuesta grabada en audio."""

    session_id: UUID
    audio_bytes: bytes
    mime_type: str
    filename: str


@dataclass(frozen=True)
class SubmitTextTurnCommand:
    """Comando para evaluar una respuesta ingresada o corregida como texto."""

    session_id: UUID
    transcript_text: str


@dataclass(frozen=True)
class DefenseSessionView:
    """Vista agregada de sesión, turnos y pregunta activa."""

    session: DefenseSession
    turns: list[DefenseTurn]
    active_question_text: str
    is_follow_up_pending: bool


@dataclass(frozen=True)
class TurnSubmissionResult:
    """Resultado completo tras evaluar un turno de sustentación."""

    session: DefenseSession
    evaluated_turn: DefenseTurn
    turns: list[DefenseTurn]
    next_question_text: str | None
    is_follow_up_pending: bool
    is_completed: bool


@dataclass(frozen=True)
class ActaExportResult:
    """Archivo binario del acta generada listo para descarga HTTP."""

    content: bytes
    mime_type: str
    filename: str
