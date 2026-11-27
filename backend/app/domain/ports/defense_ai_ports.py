"""Puertos hacia los servicios de IA de diálogo, síntesis TTS y transcripción STT."""
from dataclasses import dataclass
from typing import Protocol

from app.domain.entities.defense_session import DefenseTurn, PlannedQuestion
from app.domain.entities.fdc_analysis import FdcAnalysis
from app.domain.entities.fdc_document import FdcType
from app.domain.entities.project import Project
from app.domain.entities.rubric import RubricDefinition
from app.domain.strategies.jury_profile_strategy import JuryProfileStrategy


@dataclass(frozen=True)
class DefensePreparationInput:
    """Insumos documentales para planificar las 4 preguntas base."""

    project: Project
    fdc_type: FdcType
    analysis: FdcAnalysis
    jury_strategy: JuryProfileStrategy


@dataclass(frozen=True)
class DefensePreparationResult:
    """Preguntas base generadas y vocabulario técnico para STT."""

    questions: list[PlannedQuestion]
    custom_vocabulary: list[str]
    model_used: str
    latency_ms: int


@dataclass(frozen=True)
class TurnEvaluationInput:
    """Contexto completo para evaluar la respuesta de un turno."""

    project: Project
    fdc_type: FdcType
    analysis: FdcAnalysis
    rubric: RubricDefinition
    jury_strategy: JuryProfileStrategy
    question: PlannedQuestion
    asked_text: str
    student_transcript: str
    is_follow_up_turn: bool
    previous_turns: list[DefenseTurn]
    next_planned_question: PlannedQuestion | None = None


@dataclass(frozen=True)
class TurnEvaluationResult:
    """Juicio evaluativo estructurado por criterio y decisión de seguimiento."""

    criterion_scores: dict[str, tuple[float, str]]
    turn_feedback: str
    strengths: list[str]
    improvements: list[str]
    ai_recommends_follow_up: bool
    follow_up_question: str | None
    transition_message: str
    model_used: str
    latency_ms: int


@dataclass(frozen=True)
class SynthesizedAudio:
    """Audio sintetizado de AURA listo para entregar al cliente."""

    audio_bytes: bytes
    mime_type: str
    model_used: str


@dataclass(frozen=True)
class TranscriptionResult:
    """Texto transcrito desde el audio del sustentante."""

    transcript: str
    model_used: str
    latency_ms: int


class DefenseAiDialogPort(Protocol):
    """Puerto de generación de preguntas y evaluación semántica de turnos."""

    def generate_session_plan(self, payload: DefensePreparationInput) -> DefensePreparationResult:
        """Genera 4 preguntas base personalizadas y vocabulario técnico."""

    def evaluate_turn(self, payload: TurnEvaluationInput) -> TurnEvaluationResult:
        """Evalúa una respuesta contra la rúbrica UTS y el FDC."""


class SpeechTtsPort(Protocol):
    """Puerto de síntesis de voz humanizada (TTS)."""

    def synthesize(self, text: str) -> SynthesizedAudio:
        """Convierte el texto de AURA en audio binario WAV/MP3."""


class SpeechSttPort(Protocol):
    """Puerto de reconocimiento de voz (STT)."""

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        filename: str,
        custom_vocabulary: list[str],
    ) -> TranscriptionResult:
        """Transcribe la grabación del estudiante usando vocabulario del FDC."""
