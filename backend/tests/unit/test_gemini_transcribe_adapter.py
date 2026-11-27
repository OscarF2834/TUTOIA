"""Pruebas unitarias de GeminiTranscribeAdapter y vocabulario personalizado."""
from types import SimpleNamespace

import pytest

from app.domain.exceptions.defense_exceptions import (
    AudioTooLargeError,
    EmptyAudioError,
    UnintelligibleAudioError,
    UnsupportedAudioFormatError,
)
from app.infrastructure.adapters.gemini_transcribe_adapter import GeminiTranscribeAdapter


class _FakeInteractions:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output_text)


def test_transcribe_injects_language_and_capped_custom_vocabulary() -> None:
    fake_interactions = _FakeInteractions("TutoIA usa FastAPI y SQLAlchemy en las UTS.")
    fake_client = SimpleNamespace(interactions=fake_interactions)
    adapter = GeminiTranscribeAdapter(
        api_key="test-key",
        model="gemini-3.5-transcribe",
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
    assert result.model_used == "gemini-3.5-transcribe"
    call = fake_interactions.calls[0]
    assert call["model"] == "gemini-3.5-transcribe"
    assert call["input"][0]["mime_type"] == "audio/webm"
    tcfg = call["generation_config"]["transcription_config"]
    assert tcfg["language_codes"] == ["es-CO"]
    assert len(tcfg["custom_vocabulary"]) == 50
    assert tcfg["custom_vocabulary"][0] == "Termino0"


def test_transcribe_validates_empty_oversized_unsupported_and_unintelligible() -> None:
    fake_client = SimpleNamespace(interactions=_FakeInteractions("   "))
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
