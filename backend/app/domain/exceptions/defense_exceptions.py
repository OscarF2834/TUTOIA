"""Excepciones semánticas del dominio de sustentación oral (Módulo 2)."""
from typing import Any

from app.domain.exceptions.fdc_exceptions import FdcDomainError


class InvalidDefenseStateTransitionError(FdcDomainError):
    """La acción solicitada no es válida para el estado actual de la sesión."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_INVALID_STATE_TRANSITION", context=context)


class DefenseSessionNotFoundError(FdcDomainError):
    """No existe una sesión de sustentación para el identificador indicado."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_SESSION_NOT_FOUND", context=context)


class UnsupportedJuryProfileError(FdcDomainError):
    """El perfil de jurado solicitado no está registrado."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_UNSUPPORTED_JURY_PROFILE", context=context)


class EmptyAudioError(FdcDomainError):
    """El archivo de audio enviado está vacío."""

    def __init__(self, message: str = "La grabación de audio está vacía.", context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_EMPTY_AUDIO", context=context)


class AudioTooLargeError(FdcDomainError):
    """El archivo de audio excede el tamaño máximo permitido."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_AUDIO_TOO_LARGE", context=context)


class UnsupportedAudioFormatError(FdcDomainError):
    """El formato o MIME de audio no es compatible con Gemini Transcribe."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_UNSUPPORTED_AUDIO_FORMAT", context=context)


class UnintelligibleAudioError(FdcDomainError):
    """No fue posible transcribir habla inteligible en el audio."""

    def __init__(
        self,
        message: str = "No se detectó voz inteligible en la grabación. Intenta hablar más cerca del micrófono o escribe tu respuesta.",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="DEFENSE_UNINTELLIGIBLE_AUDIO", context=context)


class TranscriptTooShortError(FdcDomainError):
    """La respuesta transcrita o escrita no alcanza el mínimo de palabras analizables."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_TRANSCRIPT_TOO_SHORT", context=context)


class InvalidSpeechInputError(FdcDomainError):
    """El texto solicitado para síntesis TTS no pertenece a la sesión."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_INVALID_SPEECH_INPUT", context=context)


class DefenseSessionNotCompletedError(FdcDomainError):
    """La sesión de sustentación aún no concluye y no puede generar acta oficial."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DEFENSE_SESSION_NOT_COMPLETED", context=context)
