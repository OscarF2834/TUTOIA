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
            "Analizas propuestas de trabajo de grado en etapa de formulación y planeación (formato oficial F-DC-124) "
            "conforme a la Rejilla de Evaluación de Propuesta UTS: claridad del problema y pregunta de investigación, "
            "solidez de la justificación y aportes, coherencia título ↔ objetivo general ↔ objetivos específicos, "
            "pertinencia del estado del arte y fundamento teórico, y viabilidad de resultados esperados, plan de actividades, "
            "presupuesto y consideraciones éticas. "
            "Regla explícita: en un F-DC-124 está PROHIBIDO penalizar o reportar como vacío de severidad ALTA la ausencia "
            "de software implementado, datos empíricos finales o validaciones ya ejecutadas. "
            "Formula los puntos de indagación (detected_gaps_for_defense) como focos constructivos de aclaración sobre la "
            "planeación y viabilidad, nunca como reproches de ejecución. "
            "Usa únicamente evidencia explícita del contenido diligenciado por los autores; no inventes datos ni métricas. "
            "Ignora estrictamente secciones administrativas o residuales de plantilla: Información sobre el pago "
            "de la modalidad (LQ, Nequi, Bancolombia, comprobantes), REJILLA DE EVALUACIÓN, espacio del comité "
            "de trabajo de grado, firmas, cláusula de tratamiento de datos personales, ANEXO A (Turnitin), "
            "ANEXO B y ANEXO C (Instructivo General junto con sus tablas/textos de ejemplo). "
            f"{self.modality_guidance()}"
        )

    def build_analysis_prompt(self) -> str:
        return (
            "Analiza integralmente esta propuesta oficial F-DC-124 de las UTS (etapa de formulación y planeación). "
            "Desde la 'Ficha técnica de la propuesta', extrae título, modalidad marcada con X/x "
            "(Proyecto de Investigación, Desarrollo Tecnológico, Monografía o Emprendimiento), programa "
            "académico, director y únicamente los autores diligenciados con su cédula en student_code "
            "(ignorando filas vacías como Estudiante 3 o Codirector sin diligenciar). "
            "Ten presente que el F-DC-124 no exige una sección titulada literalmente 'Metodología': "
            "extrae las fases planeadas, entregables esperados, herramientas propuestas y enfoque técnico desde el "
            "Plan de actividades (cronograma por fases), Resultados esperados, Objetivos, Estado del arte, "
            "Fundamento Teórico, Presupuesto y Consideraciones éticas, sin exigir resultados ni pruebas ya ejecutadas. "
            "Ignora pagos/consignaciones, rejilla de evaluación, firmas, tratamiento de datos y Anexos A/B/C. "
            "Evalúa según la Rejilla UTS la coherencia título ↔ objetivo general ↔ objetivos específicos, "
            "justificación, fundamento teórico y viabilidad del plan; e identifica entre 3 y 6 focos constructivos "
            "de aclaración sobre planeación y viabilidad para la sustentación (sin marcar como severidad ALTA la falta de implementación)."
        )
