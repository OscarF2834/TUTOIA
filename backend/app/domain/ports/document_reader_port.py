"""Puerto para lectura e inspección estructural de documentos PDF/DOCX."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractedDocument:
    """Resultado de extracción preliminar de texto y páginas."""

    text: str
    page_count: int | None = None


class DocumentReaderPort(Protocol):
    """Contrato para extraer texto verificable de documentos binarios."""

    def extract(self, content: bytes, extension: str) -> ExtractedDocument:
        """Extrae texto y conteo de páginas según la extensión (.pdf/.docx)."""
