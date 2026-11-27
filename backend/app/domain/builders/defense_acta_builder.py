"""Patrón Builder + Director para generar Actas de Sustentación UTS (PDF/DOCX)."""
from abc import ABC, abstractmethod

from app.domain.builders.acta_report_data import ActaReportData


class DefenseActaBuilder(ABC):
    """Contrato abstracto de construcción paso a paso del Acta de Sustentación."""

    @abstractmethod
    def reset(self) -> None:
        """Reinicia el estado interno del constructor antes de ensamblar un acta."""

    @abstractmethod
    def add_institutional_header(self, data: ActaReportData) -> None:
        """Agrega encabezado oficial UTS, código de acta y fecha de emisión."""

    @abstractmethod
    def add_project_metadata(self, data: ActaReportData) -> None:
        """Agrega ficha técnica del trabajo de grado y sustentantes."""

    @abstractmethod
    def add_rubric_evaluation(self, data: ActaReportData) -> None:
        """Agrega nota global, veredicto y tabla ponderada de criterios UTS."""

    @abstractmethod
    def add_qualitative_feedback(self, data: ActaReportData) -> None:
        """Agrega mensaje de cierre, fortalezas y oportunidades de mejora."""

    @abstractmethod
    def add_defense_transcript(self, data: ActaReportData) -> None:
        """Agrega bitácora cronológica de preguntas, respuestas y retroalimentación."""

    @abstractmethod
    def add_hitl_and_signatures(self, data: ActaReportData) -> None:
        """Agrega cláusula ética Human-in-the-Loop y espacios de firma del jurado."""

    @abstractmethod
    def build(self) -> bytes:
        """Finaliza la construcción y retorna los bytes listos para descarga."""


class DefenseActaDirector:
    """Director que garantiza estructura y orden idénticos en PDF y DOCX."""

    def __init__(self, builder: DefenseActaBuilder) -> None:
        self._builder = builder

    def construct(self, data: ActaReportData) -> bytes:
        """Ejecuta los 6 pasos constructivos en secuencia obligatoria."""
        self._builder.reset()
        self._builder.add_institutional_header(data)
        self._builder.add_project_metadata(data)
        self._builder.add_rubric_evaluation(data)
        self._builder.add_qualitative_feedback(data)
        self._builder.add_defense_transcript(data)
        self._builder.add_hitl_and_signatures(data)
        return self._builder.build()
