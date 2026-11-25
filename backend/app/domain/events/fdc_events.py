"""Eventos de dominio del módulo de ingesta FDC."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class FdcDocumentAnalyzedEvent:
    """Emitido cuando un documento FDC supera la ingesta y análisis IA."""

    document_id: UUID
    project_id: UUID
    fdc_type: str
    strategy_name: str
    latency_ms: int
    occurred_at: datetime


@dataclass(frozen=True)
class FdcIngestionFailedEvent:
    """Emitido cuando la ingesta o análisis FDC falla con error controlado."""

    filename: str
    error_code: str
    occurred_at: datetime
