"""Fábrica concreta de constructores de Actas UTS (PDF y DOCX)."""
from collections.abc import Callable

from app.domain.builders.acta_report_data import ActaExportFormat
from app.domain.builders.defense_acta_builder import DefenseActaBuilder
from app.infrastructure.builders.docx_acta_builder import DocxActaBuilder
from app.infrastructure.builders.pdf_acta_builder import PdfActaBuilder

_BUILDER_REGISTRY: dict[ActaExportFormat, Callable[[], DefenseActaBuilder]] = {
    ActaExportFormat.PDF: PdfActaBuilder,
    ActaExportFormat.DOCX: DocxActaBuilder,
}


class ActaBuilderFactory:
    """Implementa ActaBuilderFactoryPort sin condicionales dispersos."""

    def create(self, export_format: ActaExportFormat) -> DefenseActaBuilder:
        """Retorna una instancia fresca del builder correspondiente al formato."""
        builder_cls = _BUILDER_REGISTRY[export_format]
        return builder_cls()
