"""Puerto de fábrica para obtener constructores concretos de Actas UTS."""
from typing import Protocol

from app.domain.builders.acta_report_data import ActaExportFormat
from app.domain.builders.defense_acta_builder import DefenseActaBuilder


class ActaBuilderFactoryPort(Protocol):
    """Fábrica abstracta desacoplada para resolver el builder por formato."""

    def create(self, export_format: ActaExportFormat) -> DefenseActaBuilder:
        """Retorna una instancia fresca de DefenseActaBuilder para el formato pedido."""
