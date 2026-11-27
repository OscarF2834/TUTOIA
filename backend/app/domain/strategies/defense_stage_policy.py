"""Política pura de etapa documental (Propuesta F-DC-124 vs Informe Final F-DC-125)."""
from abc import ABC, abstractmethod

from app.domain.entities.fdc_document import FdcType


def _team_arc_instruction(student_name: str, is_team: bool) -> str:
    if not is_team:
        return ""
    return (
        f" Sustentación en equipo con {student_name}: saluda a todos los integrantes por su nombre, "
        "dirígete a ustedes en plural natural ('bienvenidos', 'cuéntenme', 'ustedes') e involúcralos de forma equilibrada."
    )


class DefenseStagePolicy(ABC):
    """Encapsula tono temporal (prospectivo vs retrospectivo) según etapa del FDC."""

    @property
    @abstractmethod
    def fdc_type(self) -> FdcType:
        """Formato FDC gobernado por esta política."""

    @abstractmethod
    def default_source_section(self, index: int) -> str:
        """Sección documental por defecto para cada pregunta base (0..3)."""

    @abstractmethod
    def build_question_arc(
        self, student_name: str, project_title: str, is_team: bool = False
    ) -> str:
        """Arco conversacional de 4 preguntas acorde a la etapa del proyecto."""

    @abstractmethod
    def build_evaluation_stage_rules(self) -> str:
        """Criterios y prohibiciones temporales al calificar cada intervención."""


class ProposalStagePolicy(DefenseStagePolicy):
    """Etapa F-DC-124: formulación y planeación (enfoque prospectivo / futuro)."""

    _SECTIONS = {
        0: "Descripción del problema · F-DC-124",
        1: "Justificación y aportes · F-DC-124",
        2: "Objetivos y plan de actividades · F-DC-124",
        3: "Resultados esperados y alcance · F-DC-124",
    }

    @property
    def fdc_type(self) -> FdcType:
        return FdcType.FDC_124

    def default_source_section(self, index: int) -> str:
        return self._SECTIONS.get(index, "Propuesta F-DC-124")

    def build_question_arc(
        self, student_name: str, project_title: str, is_team: bool = False
    ) -> str:
        verb_greet = "bienvenidos" if is_team else "bienvenido"
        return (
            "ETAPA F-DC-124 (PROPUESTA EN PLANEACIÓN — ENFOQUE PROSPECTIVO/FUTURO): "
            "El proyecto aún NO ha sido desarrollado ni validado en campo. Está PROHIBIDO preguntar "
            "como si el sistema ya estuviera construido o exigir evidencia empírica final o pruebas ya ejecutadas. "
            "Diseña las 4 preguntas base (índices 0 a 3) para evaluar dominio de formulación y viabilidad: "
            f"0=PROBLEMA (saluda cálidamente a {student_name} con '{verb_greet}', menciona '{project_title}' e invítales a explicar con sus palabras qué problemática identificaron en las UTS y qué pregunta buscan responder); "
            "1=FUNDAMENTACION (pregunta por la justificación: por qué eligieron esta propuesta y cuáles son sus aportes principales —tecnológico, académico, institucional o social—); "
            "2=METODOLOGIA_O_PLAN (indaga cómo se articulan los objetivos específicos con las fases del plan de actividades y qué enfoque técnico planean usar); "
            "3=RESULTADOS_O_VALIDACION (indaga qué entregables concretos esperan obtener al finalizar y cómo planean validarlos, considerando viabilidad y aspectos éticos)."
            f"{_team_arc_instruction(student_name, is_team)}"
        )

    def build_evaluation_stage_rules(self) -> str:
        return (
            "REGLA DE ETAPA F-DC-124 (PROPUESTA): NUNCA bajes la calificación porque el estudiante hable "
            "en futuro ('vamos a desarrollar', 'se planea validar', 'esperamos obtener') ni porque aún no "
            "existan resultados ejecutados o software terminado. Evalúa comprensión del problema, claridad "
            "argumentativa, viabilidad del plan de actividades y coherencia con lo escrito en su F-DC-124."
        )


class FinalReportStagePolicy(DefenseStagePolicy):
    """Etapa F-DC-125: informe final ejecutado (enfoque retrospectivo / pasado)."""

    _SECTIONS = {
        0: "Planteamiento del problema · F-DC-125",
        1: "Justificación y marco teórico · F-DC-125",
        2: "Objetivos y metodología ejecutada · F-DC-125",
        3: "Resultados y conclusiones · F-DC-125",
    }

    @property
    def fdc_type(self) -> FdcType:
        return FdcType.FDC_125

    def default_source_section(self, index: int) -> str:
        return self._SECTIONS.get(index, "Informe Final F-DC-125")

    def build_question_arc(
        self, student_name: str, project_title: str, is_team: bool = False
    ) -> str:
        verb_greet = "bienvenidos" if is_team else "bienvenido"
        return (
            "ETAPA F-DC-125 (INFORME FINAL EJECUTADO — ENFOQUE RETROSPECTIVO/PASADO): "
            "El proyecto ya fue desarrollado y culminado. Diseña 4 preguntas base (índices 0 a 3) sobre ejecución real: "
            f"0=PROBLEMA (saluda cálidamente a {student_name} con '{verb_greet}', menciona '{project_title}' e invítales a explicar qué problema real abordaron y resolvieron); "
            "1=FUNDAMENTACION (pregunta por la justificación y los referentes teóricos/tecnológicos que fundamentaron la solución desarrollada); "
            "2=METODOLOGIA_O_PLAN (indaga qué se desarrolló realmente y cómo aplicaron el diseño metodológico y arquitectura para cumplir los objetivos); "
            "3=RESULTADOS_O_VALIDACION (indaga qué resultados concretos arrojaron las pruebas o validación y qué conclusiones sustentan el cierre)."
            f"{_team_arc_instruction(student_name, is_team)}"
        )

    def build_evaluation_stage_rules(self) -> str:
        return (
            "REGLA DE ETAPA F-DC-125 (INFORME FINAL): Evalúa el dominio sobre el proyecto ejecutado en pasado: "
            "evidencia concreta de lo desarrollado, aplicación efectiva de la metodología y arquitectura, "
            "resultados obtenidos en pruebas/validación y coherencia con las conclusiones reportadas en el F-DC-125."
        )


_STAGE_POLICIES: dict[FdcType, DefenseStagePolicy] = {
    FdcType.FDC_124: ProposalStagePolicy(),
    FdcType.FDC_125: FinalReportStagePolicy(),
}


def resolve_defense_stage_policy(fdc_type: FdcType) -> DefenseStagePolicy:
    """Retorna la política de etapa correspondiente al formato FDC."""
    return _STAGE_POLICIES[fdc_type]
