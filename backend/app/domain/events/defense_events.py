"""Eventos de dominio del Módulo 2 (sustentación oral)."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DefenseSessionCreatedEvent:
    """Emitido cuando se crea y prepara una sesión de sustentación."""

    session_id: UUID
    fdc_document_id: UUID
    jury_profile: str
    occurred_at: datetime


@dataclass(frozen=True)
class DefenseTurnEvaluatedEvent:
    """Emitido tras evaluar una intervención del estudiante."""

    session_id: UUID
    turn_number: int
    question_index: int
    is_follow_up: bool
    weighted_score: float
    latency_ms: int
    occurred_at: datetime


@dataclass(frozen=True)
class DefenseSessionCompletedEvent:
    """Emitido cuando la sustentación completa sus 4 ejes y emite veredicto."""

    session_id: UUID
    overall_score: float
    verdict: str
    occurred_at: datetime
