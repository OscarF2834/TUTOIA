"""Puerto para subida multimodal y análisis estructurado con IA."""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.entities.fdc_analysis import ExecutionMetrics, FdcExtraction
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy


@dataclass(frozen=True)
class RemoteFileRef:
    """Referencia al documento indexado en Gemini Files API."""

    name: str
    uri: str
    mime_type: str
    expires_at: datetime


class AiFdcAnalyzerPort(Protocol):
    """Contrato de integración hacia el motor de IA multimodal."""

    model_name: str

    def upload_document(
        self,
        content: bytes,
        mime_type: str,
        display_name: str,
        extracted_text: str,
    ) -> RemoteFileRef:
        """Sube el documento al almacenamiento remoto del proveedor IA."""

    def analyze(
        self,
        file_ref: RemoteFileRef,
        strategy: FdcAnalysisStrategy,
        model_override: str | None = None,
    ) -> tuple[FdcExtraction, ExecutionMetrics]:
        """Ejecuta el análisis estructurado aplicando la estrategia dada."""
