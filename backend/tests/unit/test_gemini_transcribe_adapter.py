"""Pruebas unitarias de GeminiTranscribeAdapter (audio multimodal generate_content)."""
from types import SimpleNamespace

import pytest

from app.domain.exceptions.defense_exceptions import (
    AudioTooLargeError,
    EmptyAudioError,
    UnintelligibleAudioError,
    UnsupportedAudioFormatError,
)
from app.domain.exceptions.fdc_exceptions import AiProviderUnavailableError
from app.infrastructure.adapters.gemini_transcribe_adapter import GeminiTranscribeAdapter


class _FakeModels:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        next_item = self._responses.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        return SimpleNamespace(text=next_item)


def test_transcribe_multimodal_injects_vocabulary_and_normalizes_mime() -> None:
    fake_models = _FakeModels(["TutoIA usa FastAPI y SQLAlchemy en las UTS."])
    fake_client = SimpleNamespace(models=fake_models)
    adapter = GeminiTranscribeAdapter(
        api_key="test-key",
        model="gemini-3.5-flash-lite",
        fallback_models=["gemini-3.8-flash"],
        client_factory=lambda: fake_client,
    )

    vocab = [f"Termino{i}" for i in range(60)]
    result = adapter.transcribe(
        audio_bytes=b"WEBM_FAKE_BYTES",
        mime_type="audio/webm;codecs=opus",
        filename="respuesta.webm",
        custom_vocabulary=vocab,
    )

    assert result.transcript == "TutoIA usa FastAPI y SQLAlchemy en las UTS."
    assert result.model_used == "gemini-3.5-flash-lite"
    call = fake_models.calls[0]
    assert call["model"] == "gemini-3.5-flash-lite"
    audio_part, prompt = call["contents"]
    assert audio_part.inline_data.mime_type == "audio/webm"
    assert audio_part.inline_data.data == b"WEBM_FAKE_BYTES"
    assert "Termino0" in prompt
    assert "Termino49" in prompt
    assert "Termino50" not in prompt


def test_transcribe_failover_logs_detail_and_recovers_with_fallback_model(caplog) -> None:
    fake_models = _FakeModels([RuntimeError("503 Service Unavailable"), "Respuesta transcrita."])
    fake_client = SimpleNamespace(models=fake_models)
    adapter = GeminiTranscribeAdapter(
        api_key="test-key",
        model="gemini-3.5-flash-lite",
        fallback_models=["gemini-3.8-flash"],
        max_retries=0,
        base_delay_seconds=0.0,
        client_factory=lambda: fake_client,
    )

    result = adapter.transcribe(b"WEBM", "audio/webm", "resp.webm", ["TutoIA"])
    assert result.transcript == "Respuesta transcrita."
    assert result.model_used == "gemini-3.8-flash"
    assert "RuntimeError" in caplog.text


def test_transcribe_validates_empty_oversized_unsupported_and_unintelligible() -> None:
    fake_client = SimpleNamespace(models=_FakeModels(["   "]))
    adapter = GeminiTranscribeAdapter(
        api_key="test-key",
        max_audio_bytes=10,
        client_factory=lambda: fake_client,
    )

    with pytest.raises(EmptyAudioError):
        adapter.transcribe(b"", "audio/webm", "vacio.webm", [])

    with pytest.raises(AudioTooLargeError):
        adapter.transcribe(b"0" * 11, "audio/webm", "grande.webm", [])

    with pytest.raises(UnsupportedAudioFormatError):
        adapter.transcribe(b"1234", "video/mp4", "video.mp4", [])

    with pytest.raises(UnintelligibleAudioError):
        adapter.transcribe(b"1234", "audio/wav", "silencio.wav", [])


def test_transcribe_all_models_fail_exposes_real_reason(caplog) -> None:
    fake_client = SimpleNamespace(models=_FakeModels([ValueError("Audio corrupto en payload")]))
    adapter = GeminiTranscribeAdapter(
        api_key="test-key",
        model="gemini-3.5-flash-lite",
        max_retries=0,
        base_delay_seconds=0.0,
        client_factory=lambda: fake_client,
    )
    with pytest.raises(AiProviderUnavailableError) as exc_info:
        adapter.transcribe(b"1234", "audio/webm", "bad.webm", [])
    assert exc_info.value.context["attempted_models"] == ["gemini-3.5-flash-lite"]
    assert "ValueError" in caplog.text
    assert "Audio corrupto en payload" in caplog.text
