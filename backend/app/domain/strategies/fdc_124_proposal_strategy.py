"""Estrategia concreta para Propuesta de Trabajo de Grado (F-DC-124)."""
from app.domain.entities.fdc_document import FdcType
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy


class Fdc124ProposalStrategy(FdcAnalysisStrategy):
    """Reglas estructurales y criterios de análisis para formato F-DC-124."""

    @property
    def name(self) -> str:
        return "Fdc124ProposalStrategy"

    @property
    def fdc_type(self) -> FdcType:
        return FdcType.FDC_124

    @property
    def required_sections(self) -> dict[str, tuple[str, ...]]:
        return {
            "problema": (
                "planteamiento del problema",
                "formulacion del problema",
                "problema",
            ),
            "objetivos": (
                "objetivo general",
                "objetivos especificos",
                "objetivos",
            ),
            "metodologia": (
                "metodologia",
                "diseno metodologico",
                "marco metodologico",
            ),
        }

    def build_system_instruction(self) -> str:
        return (
            "Eres un evaluador académico experto de las Unidades Tecnológicas de Santander (UTS). "
            "Analizas propuestas de trabajo de grado en formato F-DC-124. "
            "Usa únicamente evidencia explícita del documento adjunto; no inventes datos, citas ni métricas. "
            "Si un dato no aparece en el documento, indícalo con claridad o usa null según el esquema. "
            f"{self.modality_guidance()}"
        )

    def build_analysis_prompt(self) -> str:
        return (
            "Analiza integralmente esta propuesta F-DC-124. Extrae título, autores, director, programa, "
            "modalidad, planteamiento del problema, objetivo general, objetivos específicos y diseño metodológico "
            "propuesto (sin exigir resultados ejecutados, pues corresponde a una propuesta). "
            "Evalúa la coherencia interna entre problema, objetivos y metodología, e identifica entre 3 y 6 "
            "vacíos o riesgos de factibilidad útiles para futuras preguntas de sustentación."
        )
