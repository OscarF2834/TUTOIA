"""Adaptador de reconocimiento de voz (STT) usando audio multimodal Gemini."""
from collections.abc import Callable
import logging
from pathlib import Path
import time
from typing import Any

from app.domain.exceptions.defense_exceptions import (
    AudioTooLargeError,
    EmptyAudioError,
    UnintelligibleAudioError,
    UnsupportedAudioFormatError,
)
from app.domain.exceptions.fdc_exceptions import AiProviderUnavailableError, FdcDomainError
from app.domain.ports.defense_ai_ports import TranscriptionResult
from app.infrastructure.adapters.gemini_client_helper import (
    build_gemini_client,
    execute_with_failover,
    extract_status_code,
)

logger = logging.getLogger(__name__)

_ALLOWED_AUDIO_MIMES = {
    "audio/webm": "audio/webm",
    "audio/wav": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/ogg": "audio/ogg",
    "audio/mpeg": "audio/mpeg",
    "audio/mp3": "audio/mp3",
}
_EXT_TO_MIME = {
    ".webm": "audio/webm",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".mp3": "audio/mp3",
}


class GeminiTranscribeAdapter:
    """Implementa SpeechSttPort mediante models.generate_content con audio multimodal."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash-lite",
        fallback_models: list[str] | None = None,
        max_audio_bytes: int = 20 * 1024 * 1024,
        timeout_seconds: int = 45,
        max_retries: int = 1,
        base_delay_seconds: float = 1.5,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._api_key = api_key
        primary = model.strip() or "gemini-3.5-flash-lite"
        extras = [m.strip() for m in (fallback_models or []) if m.strip() and m.strip() != primary]
        self._models = [primary, *extras]
        self._max_audio_bytes = max_audio_bytes
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds
        self._client_factory = client_factory

    def _client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory()
        return build_gemini_client(self._api_key, self._timeout_seconds, self._models[0])

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        filename: str,
        custom_vocabulary: list[str],
    ) -> TranscriptionResult:
        """Transcribe audio del sustentante en español colombiano usando vocabulario FDC."""
        if not audio_bytes:
            raise EmptyAudioError()
        if len(audio_bytes) > self._max_audio_bytes:
            max_mb = max(1, self._max_audio_bytes // (1024 * 1024))
            raise AudioTooLargeError(
                message=f"La grabación excede el máximo permitido de {max_mb} MB.",
                context={"max_mb": max_mb, "actual_bytes": len(audio_bytes)},
            )
        clean_mime = self._resolve_mime(mime_type, filename)
        clean_vocab = [term.strip() for term in custom_vocabulary if term.strip()][:50]

        started = time.perf_counter()
        transcript, used_model = execute_with_failover(
            self._models,
            self._max_retries,
            self._base_delay,
            lambda model: self._call_transcribe(model, audio_bytes, clean_mime, clean_vocab),
        )
        clean_transcript = transcript.strip()
        if not clean_transcript:
            raise UnintelligibleAudioError(context={"model": used_model})
        return TranscriptionResult(
            transcript=clean_transcript,
            model_used=used_model,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _call_transcribe(
        self,
        model: str,
        audio_bytes: bytes,
        mime_type: str,
        custom_vocabulary: list[str],
    ) -> str:
        from google.genai import types

        client = self._client()
        prompt = self._build_transcription_prompt(custom_vocabulary)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        try:
            response = client.models.generate_content(
                model=model,
                contents=[audio_part, prompt],
                config=types.GenerateContentConfig(temperature=0.0),
            )
            return getattr(response, "text", None) or ""
        except FdcDomainError:
            raise
        except Exception as exc:
            status_code = extract_status_code(exc)
            logger.warning(
                "Gemini STT falló | model=%s | status=%s | error_type=%s | detail=%s",
                model,
                status_code,
                type(exc).__name__,
                exc,
            )
            raise AiProviderUnavailableError(
                message="Error al transcribir el audio con Gemini multimodal.",
                context={
                    "reason": f"{type(exc).__name__}: {exc}",
                    "model": model,
                    "status_code": status_code,
                },
            ) from exc

    @staticmethod
    def _build_transcription_prompt(custom_vocabulary: list[str]) -> str:
        vocab_line = (
            f"Vocabulario técnico de referencia del proyecto (respeta su ortografía si aparece en el audio): {', '.join(custom_vocabulary)}."
            if custom_vocabulary
            else ""
        )
        return (
            "Eres un transcriptor literal de audio académico en español colombiano (es-CO). "
            "Transcribe exactamente palabra por palabra lo que dice el estudiante en el audio, "
            "manteniendo puntuación natural y sin resumir, corregir ideas ni añadir comentarios. "
            "Devuelve únicamente el texto transcrito en texto plano (sin comillas ni Markdown). "
            "Si el audio solo contiene silencio o ruido sin habla inteligible, devuelve una cadena vacía. "
            f"{vocab_line}"
        ).strip()

    @staticmethod
    def _resolve_mime(mime_type: str, filename: str) -> str:
        base_mime = (mime_type or "").split(";")[0].strip().lower()
        if base_mime in _ALLOWED_AUDIO_MIMES:
            return _ALLOWED_AUDIO_MIMES[base_mime]
        ext = Path(filename or "").suffix.lower()
        if ext in _EXT_TO_MIME:
            return _EXT_TO_MIME[ext]
        raise UnsupportedAudioFormatError(
            message=f"Formato de audio '{mime_type or ext or 'desconocido'}' no soportado. Use webm, wav, ogg o mp3.",
            context={"mime_type": mime_type, "filename": filename},
        )
