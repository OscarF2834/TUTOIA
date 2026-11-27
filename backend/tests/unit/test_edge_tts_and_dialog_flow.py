"""Pruebas unitarias de EdgeTtsAdapter, FallbackTtsAdapter y flujo conversacional."""
from datetime import datetime, timezone
import sys
from types import SimpleNamespace
from uuid import uuid4

from app.domain.entities.defense_enums import DefenseStateStatus, JuryProfile
from app.domain.entities.defense_session import DefenseSession, PlannedQuestion
from app.domain.entities.fdc_document import FdcType, Modality
from app.domain.entities.project import Author, Project, ProjectStatus
from app.domain.exceptions.fdc_exceptions import AiProviderUnavailableError
from app.domain.ports.defense_ai_ports import SynthesizedAudio
from app.infrastructure.adapters.edge_tts_adapter import EdgeTtsAdapter, FallbackTtsAdapter
from app.infrastructure.adapters.gemini_defense_dialog_adapter import (
    default_source_section,
    extract_student_first_name,
)


def test_edge_tts_adapter_synthesizes_colombian_male_voice(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class _FakeCommunicate:
        def __init__(self, text: str, voice: str) -> None:
            captured["text"] = text
            captured["voice"] = voice

        async def stream(self):
            yield {"type": "audio", "data": b"ID3_MP3_PART1"}
            yield {"type": "WordBoundary", "text": "Hola"}
            yield {"type": "audio", "data": b"_PART2"}

    monkeypatch.setitem(sys.modules, "edge_tts", SimpleNamespace(Communicate=_FakeCommunicate))
    adapter = EdgeTtsAdapter(voice="es-CO-GonzaloNeural")
    result = adapter.synthesize("Hola Pedro, bienvenido a tu sustentación.")

    assert result.mime_type == "audio/mpeg"
    assert result.model_used == "edge-tts:es-CO-GonzaloNeural"
    assert result.audio_bytes == b"ID3_MP3_PART1_PART2"
    assert captured["voice"] == "es-CO-GonzaloNeural"


def test_fallback_tts_adapter_uses_secondary_on_primary_failure() -> None:
    class _BrokenPrimary:
        def synthesize(self, _text: str) -> SynthesizedAudio:
            raise AiProviderUnavailableError("Red bloqueada")

    class _WorkingSecondary:
        def synthesize(self, text: str) -> SynthesizedAudio:
            return SynthesizedAudio(audio_bytes=b"RIFF_FALLBACK", mime_type="audio/wav", model_used="gemini-tts")

    adapter = FallbackTtsAdapter(
        primary=_BrokenPrimary(),
        secondary=_WorkingSecondary(),
        primary_name="edge",
        secondary_name="gemini",
    )
    out = adapter.synthesize("Pregunta de prueba.")
    assert out.model_used == "gemini-tts"
    assert out.audio_bytes == b"RIFF_FALLBACK"


def test_transition_message_combines_with_next_question_and_authorizes_tts() -> None:
    q0 = PlannedQuestion(0, "PROBLEMA", "¿Cuál es el problema?", "Claridad", source_section="Descripción del problema · F-DC-124")
    q1 = PlannedQuestion(1, "FUNDAMENTACION", "¿Por qué eligieron esta solución?", "Justificación", source_section="Justificación · F-DC-124")
    session = DefenseSession(
        id=uuid4(),
        fdc_document_id=uuid4(),
        jury_profile=JuryProfile.ESTANDAR_UTS,
        state=DefenseStateStatus.EVALUATING_TURN,
        current_question_index=0,
        planned_questions=[q0, q1],
        custom_vocabulary=[],
        created_at=datetime.now(timezone.utc),
    )

    session.advance_to_next_question("Muy bien Pedro, queda claro el contexto.")
    prompt = session.active_prompt_text([])
    assert session.current_question_index == 1
    assert prompt == "Muy bien Pedro, queda claro el contexto. ¿Por qué eligieron esta solución?"
    assert prompt in session.authorized_tts_texts([])


def test_extract_student_first_name_and_source_sections() -> None:
    now = datetime.now(timezone.utc)
    project = Project(
        id=uuid4(),
        title="TutoIA",
        academic_program="Ingeniería de Sistemas",
        modality=Modality.DESARROLLO_TECNOLOGICO,
        authors=[Author(full_name="pedro antonio perez")],
        status=ProjectStatus.ANALYZED,
        created_at=now,
        updated_at=now,
    )
    assert extract_student_first_name(project) == "Pedro"
    assert default_source_section(0, FdcType.FDC_124) == "Descripción del problema · F-DC-124"
    assert default_source_section(3, FdcType.FDC_125) == "Resultados y conclusiones · F-DC-125"
