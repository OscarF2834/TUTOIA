"""Dobles de prueba deterministas para los puertos del Módulo 2."""
from app.domain.entities.defense_session import PlannedQuestion
from app.domain.ports.defense_ai_ports import (
    DefensePreparationInput,
    DefensePreparationResult,
    SynthesizedAudio,
    TranscriptionResult,
    TurnEvaluationInput,
    TurnEvaluationResult,
)


class FakeDefenseDialogAdapter:
    """Mock programable de DefenseAiDialogPort."""

    def __init__(self, weak_first_turn: bool = False) -> None:
        self.weak_first_turn = weak_first_turn
        self.plan_calls: list[DefensePreparationInput] = []
        self.eval_calls: list[TurnEvaluationInput] = []

    def generate_session_plan(self, payload: DefensePreparationInput) -> DefensePreparationResult:
        self.plan_calls.append(payload)
        questions = [
            PlannedQuestion(
                index=0,
                thematic_axis="PROBLEMA",
                question_text="¿Cuál es el problema central de su proyecto en las UTS?",
                evaluation_focus="Claridad del problema y contexto institucional.",
            ),
            PlannedQuestion(
                index=1,
                thematic_axis="FUNDAMENTACION",
                question_text="¿Qué referentes teóricos sustentan su propuesta tecnológica?",
                evaluation_focus="Dominio de referentes teóricos.",
            ),
            PlannedQuestion(
                index=2,
                thematic_axis="METODOLOGIA_O_PLAN",
                question_text="¿Cómo ejecutó o planificó las fases metodológicas?",
                evaluation_focus="Rigor metodológico y fases.",
            ),
            PlannedQuestion(
                index=3,
                thematic_axis="RESULTADOS_O_VALIDACION",
                question_text="¿Qué resultados o criterios de validación respaldan el proyecto?",
                evaluation_focus="Evidencia de resultados y validación.",
            ),
        ]
        return DefensePreparationResult(
            questions=questions,
            custom_vocabulary=["TutoIA", "AURA", "UTS", "GRIIS", "FastAPI", "SQLAlchemy"],
            model_used="fake-dialog-model",
            latency_ms=35,
        )

    def evaluate_turn(self, payload: TurnEvaluationInput) -> TurnEvaluationResult:
        self.eval_calls.append(payload)
        is_weak = self.weak_first_turn and payload.question.index == 0
        if is_weak:
            scores = {
                "pertinencia": (2.2, "Respuesta parcial frente a la pregunta."),
                "coherencia": (2.5, "Hilo argumental básico."),
                "fundamentacion": (2.0, "Faltan referentes explícitos."),
                "metodologia": (2.2, "Falta precisión metodológica."),
            }
            return TurnEvaluationResult(
                criterion_scores=scores,
                turn_feedback="Tu respuesta requiere mayor concreción sobre el problema.",
                strengths=["Aborda el tema general."],
                improvements=["Precisar evidencia y referentes del FDC."],
                ai_recommends_follow_up=True,
                follow_up_question="¿Puedes precisar qué métrica demuestra esa inconsistencia?",
                transition_message="Pasemos al siguiente eje.",
                model_used="fake-dialog-model",
                latency_ms=40,
            )

        scores = {
            "pertinencia": (4.5, "Responde directamente a la pregunta."),
            "coherencia": (4.3, "Discurso estructurado y claro."),
            "fundamentacion": (4.2, "Cita referentes coherentes con el FDC."),
            "metodologia": (4.4, "Explica fases e instrumentos con precisión."),
        }
        return TurnEvaluationResult(
            criterion_scores=scores,
            turn_feedback="Respuesta sólida y bien fundamentada en el documento.",
            strengths=["Argumentación clara y conectada al proyecto."],
            improvements=["Profundizar en métricas adicionales en futuras iteraciones."],
            ai_recommends_follow_up=False,
            follow_up_question=None,
            transition_message="Avancemos al siguiente eje.",
            model_used="fake-dialog-model",
            latency_ms=40,
        )


class FakeTtsAdapter:
    """Mock de SpeechTtsPort que devuelve un header WAV mínimo válido."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize(self, text: str) -> SynthesizedAudio:
        self.calls.append(text)
        return SynthesizedAudio(
            audio_bytes=b"RIFF\x24\x00\x00\x00WAVEfmt ",
            mime_type="audio/wav",
            model_used="fake-tts-model",
        )


class FakeSttAdapter:
    """Mock de SpeechSttPort que registra el custom_vocabulary recibido."""

    def __init__(self, transcript: str = "Explico la arquitectura limpia y la validacion del proyecto UTS.") -> None:
        self.transcript = transcript
        self.calls: list[dict] = []

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        filename: str,
        custom_vocabulary: list[str],
    ) -> TranscriptionResult:
        self.calls.append(
            {
                "size": len(audio_bytes),
                "mime_type": mime_type,
                "filename": filename,
                "custom_vocabulary": list(custom_vocabulary),
            }
        )
        return TranscriptionResult(
            transcript=self.transcript,
            model_used="fake-transcribe-model",
            latency_ms=25,
        )
