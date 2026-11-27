"""Manejadores globales de excepciones de dominio hacia respuestas HTTP."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions.defense_exceptions import (
    AudioTooLargeError,
    DefenseSessionNotFoundError,
    EmptyAudioError,
    InvalidDefenseStateTransitionError,
    InvalidSpeechInputError,
    TranscriptTooShortError,
    UnintelligibleAudioError,
    UnsupportedAudioFormatError,
    UnsupportedJuryProfileError,
)
from app.domain.exceptions.fdc_exceptions import (
    AiProviderNotConfiguredError,
    AiProviderUnavailableError,
    AiResponseValidationError,
    CorruptedDocumentError,
    EmptyDocumentError,
    FdcDocumentNotFoundError,
    FdcDomainError,
    FileTooLargeError,
    InvalidFdcStructureError,
    UnreadableDocumentError,
    UnsupportedDocumentFormatError,
    UnsupportedFdcTypeError,
)

_EXCEPTION_STATUS_MAP: dict[type[FdcDomainError], int] = {
    EmptyDocumentError: 422,
    FileTooLargeError: 413,
    UnsupportedDocumentFormatError: 415,
    CorruptedDocumentError: 422,
    UnreadableDocumentError: 422,
    InvalidFdcStructureError: 422,
    UnsupportedFdcTypeError: 422,
    FdcDocumentNotFoundError: 404,
    AiProviderNotConfiguredError: 503,
    AiProviderUnavailableError: 502,
    AiResponseValidationError: 502,
    InvalidDefenseStateTransitionError: 409,
    DefenseSessionNotFoundError: 404,
    UnsupportedJuryProfileError: 422,
    EmptyAudioError: 422,
    AudioTooLargeError: 413,
    UnsupportedAudioFormatError: 415,
    UnintelligibleAudioError: 422,
    TranscriptTooShortError: 422,
    InvalidSpeechInputError: 422,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Registra la traducción uniforme de FdcDomainError a HTTP."""

    @app.exception_handler(FdcDomainError)
    async def handle_fdc_domain_error(_request: Request, exc: FdcDomainError) -> JSONResponse:
        status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 400)
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "context": exc.context,
            },
        )
