"""DTOs de comando, contexto de cadena y lectura del módulo FDC."""
from dataclasses import dataclass

from app.domain.entities.fdc_analysis import FdcAnalysis
from app.domain.entities.fdc_document import FdcDocument, FdcType, Modality
from app.domain.entities.project import Project
from app.domain.ports.ai_fdc_analyzer_port import RemoteFileRef
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy


@dataclass(frozen=True)
class FdcUploadCommand:
    """Comando de entrada para ingesta y análisis de un documento FDC."""

    filename: str
    content: bytes
    fdc_type: FdcType
    academic_program: str | None = None
    modality: Modality | None = None


@dataclass
class FdcIngestionContext:
    """Estado compartido a través de la Chain of Responsibility."""

    filename: str
    content: bytes
    strategy: FdcAnalysisStrategy
    extension: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    sha256: str = ""
    extracted_text: str = ""
    remote_file: RemoteFileRef | None = None


@dataclass(frozen=True)
class FdcDocumentView:
    """Vista agregada de proyecto, documento FDC y análisis."""

    project: Project
    document: FdcDocument
    analysis: FdcAnalysis
