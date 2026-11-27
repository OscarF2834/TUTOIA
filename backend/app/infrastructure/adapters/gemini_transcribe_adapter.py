"""Adaptador de reconocimiento de voz (STT) usando Gemini Transcribe."""
import base64
from collections.abc import Callable
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
    """Implementa SpeechSttPort sobre gemini-3.5-transcribe."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-transcribe",
        max_audio_bytes: int = 20 * 1024 * 1024,
        timeout_seconds: int = 45,
        max_retries: int = 1,
        base_delay_seconds: float = 1.5,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model.strip()
        self._max_audio_bytes = max_audio_bytes
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds
        self._client_factory = client_factory

    def _client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory()
        return build_gemini_client(self._api_key, self._timeout_seconds, self._model)

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
            [self._model],
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
        client = self._client()
        encoded_audio = base64.b64encode(audio_bytes).decode("ascii")
        transcription_cfg: dict[str, Any] = {"language_codes": ["es-CO"]}
        if custom_vocabulary:
            transcription_cfg["custom_vocabulary"] = custom_vocabulary

        try:
            interaction = client.interactions.create(
                model=model,
                input=[{"type": "audio", "data": encoded_audio, "mime_type": mime_type}],
                generation_config={"transcription_config": transcription_cfg},
                timeout=float(self._timeout_seconds),
            )
            return interaction.output_text or ""
        except FdcDomainError:
            raise
        except Exception as exc:
            raise AiProviderUnavailableError(
                message="Error al transcribir el audio con Gemini Transcribe.",
                context={"reason": str(exc), "model": model, "status_code": extract_status_code(exc)},
            ) from exc

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
