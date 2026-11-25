"""Contrato base Strategy para el análisis de documentos FDC."""
from abc import ABC, abstractmethod

from app.domain.entities.fdc_document import FdcType, Modality


MODALITY_EMPHASIS: dict[Modality, str] = {
    Modality.DESARROLLO_TECNOLOGICO: (
        "Enfatiza arquitectura técnica, artefacto desarrollado, requisitos y pruebas de validación."
    ),
    Modality.INVESTIGACION: (
        "Enfatiza rigurosidad metodológica, hipótesis/variables, muestra y validez de hallazgos."
    ),
    Modality.MONOGRAFIA: (
        "Enfatiza estado del arte, síntesis crítica de fuentes académicas y rigor argumentativo."
    ),
    Modality.EMPRENDIMIENTO: (
        "Enfatiza propuesta de valor, validación de mercado, viabilidad financiera y plan operativo."
    ),
}


class FdcAnalysisStrategy(ABC):
    """Estrategia abstracta de validación estructural y análisis IA por formato FDC."""

    def __init__(self, modality: Modality | None = None) -> None:
        self.modality = modality

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador estable de la estrategia ejecutada."""

    @property
    @abstractmethod
    def fdc_type(self) -> FdcType:
        """Tipo de documento FDC asociado a esta estrategia."""

    @property
    @abstractmethod
    def required_sections(self) -> dict[str, tuple[str, ...]]:
        """Mapa sección -> sinónimos normalizados (minúsculas y sin tildes)."""

    def modality_guidance(self) -> str:
        """Devuelve la directriz complementaria según modalidad si aplica."""
        if self.modality is None:
            return "Evalúa de forma equilibrada conforme al reglamento de trabajos de grado UTS."
        return MODALITY_EMPHASIS.get(
            self.modality,
            "Evalúa de forma equilibrada conforme al reglamento de trabajos de grado UTS.",
        )

    @abstractmethod
    def build_system_instruction(self) -> str:
        """Construye la instrucción del sistema para el motor de análisis."""

    @abstractmethod
    def build_analysis_prompt(self) -> str:
        """Construye el prompt específico para extraer el diagnóstico FDC."""
