"""Pruebas unitarias de EdgeTtsAdapter, FallbackTtsAdapter y diálogo calibrado por etapa."""
from datetime import datetime, timezone
import json
import sys
from types import SimpleNamespace
from uuid import uuid4

from app.domain.entities.defense_enums import DefenseStateStatus, JuryProfile
from app.domain.entities.defense_session import DefenseSession, PlannedQuestion
from app.domain.entities.fdc_analysis import (
    AcademicSynthesis,
    CoherenceFinding,
    DefenseGap,
    ExecutionMetrics,
    FdcAnalysis,
)
from app.domain.entities.fdc_document import FdcType, Modality
from app.domain.entities.project import Author, Project, ProjectStatus
from app.domain.entities.rubric import RubricCriterion, RubricDefinition
from app.domain.exceptions.fdc_exceptions import AiProviderUnavailableError
from app.domain.factories.jury_strategy_factory import JuryStrategyFactory
from app.domain.ports.defense_ai_ports import (
    DefensePreparationInput,
    SynthesizedAudio,
    TurnEvaluationInput,
)
from app.infrastructure.adapters.edge_tts_adapter import EdgeTtsAdapter, FallbackTtsAdapter
from app.infrastructure.adapters.gemini_defense_dialog_adapter import (
    GeminiDefenseDialogAdapter,
    default_source_section,
    extract_student_first_name,
)


def _sample_project_and_analysis(doc_id=None) -> tuple[Project, FdcAnalysis]:
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
    analysis = FdcAnalysis(
        id=uuid4(),
        fdc_document_id=doc_id or uuid4(),
        strategy_name="Fdc124ProposalStrategy",
        model_name="gemini-3.5-flash-lite",
        schema_version="1.0",
        academic_synthesis=AcademicSynthesis(
            central_problem="Carga operativa al evaluar sustentaciones.",
            research_question="¿Cómo apoyar la preparación de sustentaciones en las UTS?",
            justification_summary="Estandariza la retroalimentación académica.",
            general_objective="Diseñar una plataforma de apoyo a sustentaciones.",
            specific_objectives=["Analizar documentos FDC.", "Simular diálogo oral."],
            research_type_and_approach="Desarrollo tecnológico iterativo",
            phases_or_stages=["Análisis", "Diseño", "Validación"],
            technologies_and_instruments=["FastAPI", "React", "Gemini"],
            validation_scope="Prueba piloto con propuestas reales.",
            results_and_conclusions_summary="Prototipo funcional y rúbrica calibrada.",
        ),
        overall_coherence_level="ALTA",
        coherence_findings=[
            CoherenceFinding("PROBLEMA_OBJETIVOS", "SOLIDO", "Coherente.", "Sección 2.")
        ],
        detected_gaps=[
            DefenseGap("METODOLOGIA", "MEDIA", "Precisar tamaño de muestra piloto.", "Preguntar por muestra.")
        ],
        execution_metrics=ExecutionMetrics(latency_ms=100),
        created_at=now,
    )
    return project, analysis


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
        def synthesize(self, _text: str) -> SynthesizedAudio:
            return SynthesizedAudio(audio_bytes=b"RIFF_FALLBACK", mime_type="audio/wav", model_used="gemini-tts")

    adapter = FallbackTtsAdapter(_BrokenPrimary(), _WorkingSecondary(), "edge", "gemini")
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
    project, _ = _sample_project_and_analysis()
    assert extract_student_first_name(project) == "Pedro"
    assert project.is_team() is False

    now = project.created_at
    team_two = Project(uuid4(), "TutoIA", "Sistemas", Modality.DESARROLLO_TECNOLOGICO, [Author("pedro perez"), Author("oscar gomez")], ProjectStatus.ANALYZED, now, now)
    team_three = Project(uuid4(), "TutoIA", "Sistemas", Modality.DESARROLLO_TECNOLOGICO, [Author("pedro perez"), Author("oscar gomez"), Author("laura diaz")], ProjectStatus.ANALYZED, now, now)
    no_authors = Project(uuid4(), "TutoIA", "Sistemas", Modality.DESARROLLO_TECNOLOGICO, [], ProjectStatus.ANALYZED, now, now)
    assert team_two.formatted_authors_greeting() == "Pedro y Oscar"
    assert team_two.is_team() is True
    assert team_three.formatted_authors_greeting() == "Pedro, Oscar y Laura"
    assert no_authors.formatted_authors_greeting() == "estudiante"
    assert default_source_section(0, FdcType.FDC_124) == "Descripción del problema · F-DC-124"
    assert default_source_section(3, FdcType.FDC_125) == "Resultados y conclusiones · F-DC-125"


def test_dialog_adapter_includes_all_team_authors_in_plan_and_turn_eval() -> None:
    calls: list[dict] = []
    plan_json = json.dumps({
        "questions": [
            {"index": 0, "thematic_axis": "PROBLEMA", "question_text": "Hola Pedro y Oscar, bienvenidos a su sustentación.", "evaluation_focus": "Claridad del problema en las UTS."},
            {"index": 1, "thematic_axis": "FUNDAMENTACION", "question_text": "¿Por qué eligieron esta propuesta para las UTS?", "evaluation_focus": "Justificación y aportes del proyecto."},
            {"index": 2, "thematic_axis": "METODOLOGIA_O_PLAN", "question_text": "¿Cómo organizaron su plan de actividades?", "evaluation_focus": "Articulación objetivos y plan de trabajo."},
            {"index": 3, "thematic_axis": "RESULTADOS_O_VALIDACION", "question_text": "¿Qué entregables esperan obtener y cómo los validarán?", "evaluation_focus": "Viabilidad de entregables y validación."},
        ],
        "custom_vocabulary": ["TutoIA"],
    })
    eval_json = json.dumps({
        "criterion_scores": [
            {"code": "pertinencia", "score": 4.3, "rationale": "Explica bien el problema."},
            {"code": "coherencia", "score": 4.2, "rationale": "Discurso claro y ordenado."},
            {"code": "fundamentacion", "score": 4.0, "rationale": "Base conceptual sólida."},
            {"code": "metodologia", "score": 4.1, "rationale": "Plan técnico muy viable."},
        ],
        "turn_feedback": "Buen trabajo en equipo.",
        "strengths": ["Cohesión."],
        "improvements": ["Detallar cronograma."],
        "needs_follow_up": False,
        "follow_up_question": None,
        "transition_message": "Muy bien Pedro y Oscar, continuemos.",
    })
    fake_interactions = SimpleNamespace(create=lambda **kw: (calls.append(kw), SimpleNamespace(output_text=plan_json if len(calls) == 1 else eval_json))[1])
    project, analysis = _sample_project_and_analysis()
    project.authors = [Author("pedro antonio perez"), Author("oscar javier gomez")]
    adapter = GeminiDefenseDialogAdapter("k", "gemini-3.5-flash-lite", [], client_factory=lambda: SimpleNamespace(interactions=fake_interactions))

    plan = adapter.generate_session_plan(DefensePreparationInput(project, FdcType.FDC_124, analysis, JuryStrategyFactory.create(JuryProfile.ESTANDAR_UTS)))
    assert "Pedro y Oscar" in calls[0]["system_instruction"]
    assert "Sustentación en equipo" in calls[0]["system_instruction"]
    assert '"sustentantes": ["Pedro", "Oscar"]' in calls[0]["input"]
    assert '"es_equipo": true' in calls[0]["input"]

    rubric = RubricDefinition("UTS", "2026", [RubricCriterion("pertinencia", "Pertinencia", 1.0, "")])
    adapter.evaluate_turn(TurnEvaluationInput(project, FdcType.FDC_124, analysis, rubric, JuryStrategyFactory.create(JuryProfile.ESTANDAR_UTS), plan.questions[0], plan.questions[0].question_text, "Vamos a desarrollar el prototipo juntos.", False, []))
    assert "sustentación en equipo (Pedro y Oscar)" in calls[1]["system_instruction"]
    assert '"sustentantes": ["Pedro", "Oscar"]' in calls[1]["input"]


def test_dialog_adapter_calibrates_fdc_124_standard_vs_fdc_125_rigorous() -> None:
    calls: list[dict] = []
    plan_json = json.dumps({
        "questions": [
            {"index": 0, "thematic_axis": "PROBLEMA", "question_text": "Hola Pedro, cuéntame qué problema identificaron.", "evaluation_focus": "Claridad del problema."},
            {"index": 1, "thematic_axis": "FUNDAMENTACION", "question_text": "¿Cuál es la justificación principal de su propuesta?", "evaluation_focus": "Aportes UTS."},
            {"index": 2, "thematic_axis": "METODOLOGIA_O_PLAN", "question_text": "¿Cómo conectan los objetivos con su plan de actividades?", "evaluation_focus": "Articulación."},
            {"index": 3, "thematic_axis": "RESULTADOS_O_VALIDACION", "question_text": "¿Qué entregables esperan obtener y cómo planean validarlos?", "evaluation_focus": "Viabilidad."},
        ],
        "custom_vocabulary": ["TutoIA", "UTS"],
    })
    eval_json = json.dumps({
        "criterion_scores": [
            {"code": "pertinencia", "score": 4.4, "rationale": "Explica bien el problema."},
            {"code": "coherencia", "score": 4.3, "rationale": "Coherente con FDC."},
            {"code": "fundamentacion", "score": 4.1, "rationale": "Buena base conceptual."},
            {"code": "metodologia", "score": 4.2, "rationale": "Plan viable."},
        ],
        "turn_feedback": "Muy clara tu explicación del problema en las UTS.",
        "strengths": ["Claridad argumental."],
        "improvements": ["Detallar cronograma en la siguiente fase."],
        "needs_follow_up": False,
        "follow_up_question": None,
        "transition_message": "Muy bien Pedro, queda claro el enfoque que plantean.",
    })

    class _FakeInteractions:
        def __init__(self) -> None:
            self.payloads = [plan_json, eval_json, plan_json]

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_text=self.payloads.pop(0))

    fake_interactions = _FakeInteractions()
    project, analysis = _sample_project_and_analysis()
    adapter = GeminiDefenseDialogAdapter(
        api_key="k",
        model="gemini-3.5-flash-lite",
        fallback_models=[],
        client_factory=lambda: SimpleNamespace(interactions=fake_interactions),
    )

    plan_124 = adapter.generate_session_plan(
        DefensePreparationInput(project, FdcType.FDC_124, analysis, JuryStrategyFactory.create(JuryProfile.ESTANDAR_UTS))
    )
    assert plan_124.questions[0].source_section == "Descripción del problema · F-DC-124"
    assert "ENFOQUE PROSPECTIVO/FUTURO" in calls[0]["system_instruction"]
    assert "no fiscalizador" in calls[0]["system_instruction"]
    assert "vacios_detectados" not in calls[0]["input"]

    rubric = RubricDefinition("UTS", "2026", [RubricCriterion("pertinencia", "Pertinencia", 1.0, "")])
    adapter.evaluate_turn(
        TurnEvaluationInput(
            project=project,
            fdc_type=FdcType.FDC_124,
            analysis=analysis,
            rubric=rubric,
            jury_strategy=JuryStrategyFactory.create(JuryProfile.ESTANDAR_UTS),
            question=plan_124.questions[0],
            asked_text=plan_124.questions[0].question_text,
            student_transcript="Vamos a desarrollar la plataforma y planeamos validar con docentes.",
            is_follow_up_turn=False,
            previous_turns=[],
            next_planned_question=plan_124.questions[1],
        )
    )
    assert "NUNCA bajes la calificación porque el estudiante hable en futuro" in calls[1]["system_instruction"]
    assert "focos_aclaracion_apoyo" in calls[1]["input"]

    adapter.generate_session_plan(
        DefensePreparationInput(project, FdcType.FDC_125, analysis, JuryStrategyFactory.create(JuryProfile.TECNICO_RIGUROSO))
    )
    assert "ENFOQUE RETROSPECTIVO/PASADO" in calls[2]["system_instruction"]
    assert "qué resultados concretos arrojaron las pruebas" in calls[2]["system_instruction"]
    assert "vacios_detectados" in calls[2]["input"]
