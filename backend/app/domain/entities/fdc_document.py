"""Entidad FdcDocument y enumeraciones del dominio FDC."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class FdcType(StrEnum):
    """Tipos institucionales de formato FDC en las UTS."""

    FDC_124 = "FDC_124"
    FDC_125 = "FDC_125"


class Modality(StrEnum):
    """Modalidades oficiales de trabajo de grado UTS."""

    DESARROLLO_TECNOLOGICO = "DESARROLLO_TECNOLOGICO"
    INVESTIGACION = "INVESTIGACION"
    MONOGRAFIA = "MONOGRAFIA"
    EMPRENDIMIENTO = "EMPRENDIMIENTO"


class IngestionStatus(StrEnum):
    """Estados posibles del ciclo de ingesta de un archivo FDC."""

    VALIDATED = "VALIDATED"
    UPLOADED_TO_GEMINI = "UPLOADED_TO_GEMINI"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


@dataclass
class FdcDocument:
    """Representación de un documento FDC cargado e indexado."""

    id: UUID
    project_id: UUID
    fdc_type: FdcType
    original_filename: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    storage_path: str
    ingestion_status: IngestionStatus
    created_at: datetime
    gemini_file_name: str | None = None
    gemini_file_uri: str | None = None
    gemini_file_expires_at: datetime | None = None

    def is_gemini_uri_active(self, now: datetime) -> bool:
        """Indica si la referencia en Gemini Files API sigue vigente."""
        if not self.gemini_file_uri or not self.gemini_file_expires_at:
            return False
        return self.gemini_file_expires_at > now
