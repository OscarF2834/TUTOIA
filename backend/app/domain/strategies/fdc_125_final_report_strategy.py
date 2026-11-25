"""Estrategia concreta para Informe Final de Trabajo de Grado (F-DC-125)."""
from app.domain.entities.fdc_document import FdcType
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy


class Fdc125FinalReportStrategy(FdcAnalysisStrategy):
    """Reglas estructurales y criterios de análisis para formato F-DC-125."""

    @property
    def name(self) -> str:
        return "Fdc125FinalReportStrategy"

    @property
    def fdc_type(self) -> FdcType:
        return FdcType.FDC_125

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
            "resultados": ("resultados",),
            "conclusiones": ("conclusiones",),
        }

    def build_system_instruction(self) -> str:
        return (
            "Eres un jurado evaluador senior de las Unidades Tecnológicas de Santander (UTS). "
            "Analizas informes finales de trabajo de grado en formato F-DC-125. "
            "Usa únicamente evidencia real contenida en el documento adjunto; está prohibido inventar "
            "cifras, autores o conclusiones no presentes en el texto. "
            f"{self.modality_guidance()}"
        )

    def build_analysis_prompt(self) -> str:
        return (
            "Analiza exhaustivamente este informe final F-DC-125. Extrae título, autores, director, programa, "
            "modalidad, problema, objetivo general, objetivos específicos, metodología ejecutada, resultados y "
            "conclusiones. Verifica estrictamente la trazabilidad entre los objetivos planteados y los resultados "
            "y conclusiones reportados, e identifica entre 3 y 6 vacíos argumentales, metodológicos o de evidencia "
            "para formular futuras preguntas de sustentación."
        )
