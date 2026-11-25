"""Pruebas unitarias de InMemoryEventBus (patrón Observer)."""
from datetime import datetime, timezone
from uuid import uuid4

from app.application.observers.event_bus import InMemoryEventBus
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent


def test_event_bus_notifies_all_subscribers_and_isolates_failures() -> None:
    bus = InMemoryEventBus()
    received: list[FdcDocumentAnalyzedEvent] = []

    def broken_subscriber(_event: FdcDocumentAnalyzedEvent) -> None:
        raise RuntimeError("Fallo simulado de observador")

    bus.subscribe(FdcDocumentAnalyzedEvent, broken_subscriber)
    bus.subscribe(FdcDocumentAnalyzedEvent, received.append)

    event = FdcDocumentAnalyzedEvent(
        document_id=uuid4(),
        project_id=uuid4(),
        fdc_type="FDC_125",
        strategy_name="Fdc125FinalReportStrategy",
        latency_ms=15,
        occurred_at=datetime.now(timezone.utc),
    )
    bus.publish(event)
    assert received == [event]
