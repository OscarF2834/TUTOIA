"""Adaptador de síntesis de voz neuronal (TTS) usando Google Gemini."""
import base64
from collections.abc import Callable
import io
from typing import Any
import wave

from app.domain.exceptions.fdc_exceptions import AiProviderUnavailableError, FdcDomainError
from app.domain.ports.defense_ai_ports import SynthesizedAudio
from app.infrastructure.adapters.gemini_client_helper import (
    build_gemini_client,
    execute_with_failover,
    extract_status_code,
)

_FORMAL_STYLE = (
    "Tono académico universitario formal, claro, sereno y natural en español colombiano "
    "para evaluar una sustentación de trabajo de grado."
)


def _wrap_pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
    """Envuelve PCM16 mono en contenedor RIFF WAV estándar."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buf.getvalue()


def _decode_audio_payload(raw_data: bytes | str) -> bytes:
    if isinstance(raw_data, bytes):
        return raw_data
    return base64.b64decode(raw_data)


class GeminiTtsAdapter:
    """Implementa SpeechTtsPort sobre gemini-3.8-flash-lite-tts y respaldo 2.5 TTS."""

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_models: list[str],
        voice: str = "Aoede",
        timeout_seconds: int = 45,
        max_retries: int = 1,
        base_delay_seconds: float = 1.5,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._api_key = api_key
        self._models = [model.strip(), *[m.strip() for m in fallback_models if m.strip() and m.strip() != model.strip()]]
        self._voice = voice.strip() or "Aoede"
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds
        self._client_factory = client_factory

    def _client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory()
        return build_gemini_client(self._api_key, self._timeout_seconds, self._models[0])

    def synthesize(self, text: str) -> SynthesizedAudio:
        """Sintetiza el texto de AURA a audio WAV con failover automático."""
        clean_text = text.strip()
        (audio_bytes, mime_type), used_model = execute_with_failover(
            self._models,
            self._max_retries,
            self._base_delay,
            lambda model: self._synthesize_with_model(model, clean_text),
        )
        return SynthesizedAudio(audio_bytes=audio_bytes, mime_type=mime_type, model_used=used_model)

    def _synthesize_with_model(self, model: str, text: str) -> tuple[bytes, str]:
        client = self._client()
        try:
            if "2.5" in model:
                return self._call_legacy_tts(client, model, text)
            return self._call_interactions_tts(client, model, text)
        except FdcDomainError:
            raise
        except Exception as exc:
            raise AiProviderUnavailableError(
                message="Error al sintetizar voz con Gemini TTS.",
                context={"reason": str(exc), "model": model, "status_code": extract_status_code(exc)},
            ) from exc

    def _call_interactions_tts(self, client: Any, model: str, text: str) -> tuple[bytes, str]:
        interaction = client.interactions.create(
            model=model,
            input=[
                {
                    "type": "text",
                    "text": text,
                    "annotations": [{"type": "speech_metadata", "style": _FORMAL_STYLE}],
                }
            ],
            generation_config={"speech_config": {"voice": self._voice, "language": "es-CO"}},
            response_modalities=["AUDIO"],
            response_format={"type": "audio", "mime_type": "audio/wav"},
            timeout=float(self._timeout_seconds),
        )
        audio = getattr(interaction, "output_audio", None)
        raw_data = getattr(audio, "data", None)
        if not raw_data:
            raise AiProviderUnavailableError("Gemini TTS no devolvió audio.", context={"model": model})
        audio_bytes = _decode_audio_payload(raw_data)
        mime_type = getattr(audio, "mime_type", None) or "audio/wav"
        if not audio_bytes.startswith(b"RIFF") and mime_type in ("audio/wav", "audio/l16"):
            audio_bytes = _wrap_pcm_to_wav(audio_bytes)
            mime_type = "audio/wav"
        return audio_bytes, mime_type

    def _call_legacy_tts(self, client: Any, model: str, text: str) -> tuple[bytes, str]:
        from google.genai import types

        response = client.models.generate_content(
            model=model,
            contents=f"Lee con tono académico formal y pausado en español: {text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self._voice)
                    )
                ),
            ),
        )
        inline = response.candidates[0].content.parts[0].inline_data
        raw_bytes = _decode_audio_payload(inline.data)
        if not raw_bytes.startswith(b"RIFF"):
            raw_bytes = _wrap_pcm_to_wav(raw_bytes)
        return raw_bytes, "audio/wav"
