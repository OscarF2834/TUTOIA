"""Observadores y bus de eventos síncrono en memoria."""
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.domain.events.defense_events import (
    DefenseSessionCompletedEvent,
    DefenseSessionCreatedEvent,
    DefenseTurnEvaluatedEvent,
)
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent, FdcIngestionFailedEvent

logger = logging.getLogger("tutoia.events")
audit_logger = logging.getLogger("tutoia.audit")


class InMemoryEventBus:
    """Bus síncrono y ligero en memoria (patrón Observer)."""

    def __init__(self) -> None:
        self._subscribers: dict[type[Any], list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: type[Any], callback: Callable[[Any], None]) -> None:
        """Registra un suscriptor para un tipo de evento específico."""
        self._subscribers[event_type].append(callback)

    def publish(self, event: Any) -> None:
        """Notifica a los suscriptores sin propagar fallos individuales."""
        for callback in self._subscribers.get(type(event), []):
            try:
                callback(event)
            except Exception:
                logger.exception("Error ejecutando observador para %s", type(event).__name__)


class AuditLogObserver:
    """Suscriptor que registra trazas de auditoría y métricas de ingesta."""

    def on_analyzed(self, event: FdcDocumentAnalyzedEvent) -> None:
        audit_logger.info(
            "FDC analizado | doc=%s | project=%s | tipo=%s | strategy=%s | latency_ms=%d",
            event.document_id,
            event.project_id,
            event.fdc_type,
            event.strategy_name,
            event.latency_ms,
        )

    def on_failed(self, event: FdcIngestionFailedEvent) -> None:
        audit_logger.warning(
            "Fallo ingesta FDC | file=%s | code=%s",
            event.filename,
            event.error_code,
        )

    def on_defense_created(self, event: DefenseSessionCreatedEvent) -> None:
        audit_logger.info(
            "Sesión defensa creada | session=%s | doc=%s | jury=%s",
            event.session_id,
            event.fdc_document_id,
            event.jury_profile,
        )

    def on_defense_turn(self, event: DefenseTurnEvaluatedEvent) -> None:
        audit_logger.info(
            "Turno evaluado | session=%s | turn=%d | q_idx=%d | follow_up=%s | score=%.2f | latency_ms=%d",
            event.session_id,
            event.turn_number,
            event.question_index,
            event.is_follow_up,
            event.weighted_score,
            event.latency_ms,
        )

    def on_defense_completed(self, event: DefenseSessionCompletedEvent) -> None:
        audit_logger.info(
            "Sustentación completada | session=%s | overall_score=%.2f | verdict=%s",
            event.session_id,
            event.overall_score,
            event.verdict,
        )
