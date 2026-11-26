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
                "descripcion del problema",
                "planteamiento del problema",
                "formulacion del problema",
                "problema",
            ),
            "objetivos": (
                "objetivo general",
                "objetivos especificos",
                "objetivos",
            ),
            "justificacion_o_fundamento": (
                "justificacion",
                "estado del arte",
                "fundamento teorico",
                "marco teorico",
                "marco referencial",
            ),
            "plan_o_metodologia": (
                "plan de actividades",
                "cronograma",
                "resultados esperados",
                "metodologia",
                "diseno metodologico",
                "marco metodologico",
            ),
        }

    def build_system_instruction(self) -> str:
        return (
            "Eres un evaluador académico experto de las Unidades Tecnológicas de Santander (UTS). "
            "Analizas propuestas de trabajo de grado en formato oficial F-DC-124. "
            "Usa únicamente evidencia explícita del contenido diligenciado por los autores; no inventes "
            "datos, citas ni métricas. Si un dato no aparece, indícalo con claridad o usa null según el esquema. "
            "Ignora estrictamente secciones administrativas o residuales de plantilla: Información sobre el pago "
            "de la modalidad (LQ, Nequi, Bancolombia, comprobantes), REJILLA DE EVALUACIÓN, espacio del comité "
            "de trabajo de grado, firmas, cláusula de tratamiento de datos personales, ANEXO A (Turnitin), "
            "ANEXO B y ANEXO C (Instructivo General junto con sus tablas/textos de ejemplo). "
            f"{self.modality_guidance()}"
        )

    def build_analysis_prompt(self) -> str:
        return (
            "Analiza integralmente esta propuesta oficial F-DC-124 de las UTS. "
            "Desde la 'Ficha técnica de la propuesta', extrae título, modalidad marcada con X/x "
            "(Proyecto de Investigación, Desarrollo Tecnológico, Monografía o Emprendimiento), programa "
            "académico, director y únicamente los autores diligenciados con su cédula en student_code "
            "(ignorando filas vacías como Estudiante 3 o Codirector sin diligenciar). "
            "Ten presente que el F-DC-124 no exige una sección titulada literalmente 'Metodología': "
            "extrae las fases, entregables, herramientas y enfoque técnico desde el Plan de actividades "
            "(cronograma por fases), Resultados esperados, Objetivos, Estado del arte y Fundamento Teórico "
            "(sin exigir resultados ejecutados, pues es una propuesta). "
            "Ignora pagos/consignaciones, rejilla de evaluación, firmas, tratamiento de datos y Anexos A/B/C. "
            "Evalúa la coherencia interna entre problema, objetivos, fundamento y plan de actividades, "
            "e identifica entre 3 y 6 vacíos o riesgos de factibilidad para futuras preguntas de sustentación."
        )
