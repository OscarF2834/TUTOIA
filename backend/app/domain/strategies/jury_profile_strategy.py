"""Patrón Strategy para perfiles de jurado y política de contrapregunta."""
from abc import ABC, abstractmethod

from app.domain.entities.defense_enums import JuryProfile
from app.domain.entities.fdc_document import FdcType
from app.domain.strategies.defense_stage_policy import resolve_defense_stage_policy


def _team_eval_note(student_name: str, is_team: bool) -> str:
    if not is_team:
        return ""
    return (
        f" Al ser sustentación en equipo ({student_name}), dirige la transición y retroalimentación a todos "
        "los integrantes en plural natural (sin centrarte únicamente en una sola persona)."
    )


class JuryProfileStrategy(ABC):
    """Define rigor de evaluación, tono conversacional y umbral de contrapregunta."""

    @property
    @abstractmethod
    def profile(self) -> JuryProfile:
        """Identificador del perfil de jurado."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre descriptivo de la estrategia."""

    @property
    @abstractmethod
    def follow_up_score_threshold(self) -> float:
        """Nota ponderada bajo la cual se dispara una contrapregunta."""

    @property
    @abstractmethod
    def include_gaps_in_base_questions(self) -> bool:
        """Indica si las preguntas base deben inyectar detected_gaps como foco crítico."""

    @abstractmethod
    def build_question_generation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante", is_team: bool = False
    ) -> str:
        """Directrices para generar las 4 preguntas base según formato y jurado."""

    @abstractmethod
    def build_turn_evaluation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante", is_team: bool = False
    ) -> str:
        """Directrices para evaluar la respuesta del estudiante y generar transición."""

    def should_trigger_follow_up(
        self,
        already_followed_up: bool,
        weighted_score: float,
        ai_recommends_follow_up: bool,
        follow_up_text: str | None,
    ) -> bool:
        """Garantiza máximo 1 contrapregunta por pregunta base."""
        if already_followed_up:
            return False
        if not (follow_up_text or "").strip():
            return False
        return ai_recommends_follow_up or (weighted_score < self.follow_up_score_threshold)


class StandardUtsJuryStrategy(JuryProfileStrategy):
    """Jurado institucional cercano, no adversarial y equilibrado conforme a la rúbrica UTS."""

    @property
    def profile(self) -> JuryProfile:
        return JuryProfile.ESTANDAR_UTS

    @property
    def name(self) -> str:
        return "StandardUtsJuryStrategy"

    @property
    def follow_up_score_threshold(self) -> float:
        return 3.5

    @property
    def include_gaps_in_base_questions(self) -> bool:
        return False

    def build_question_generation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante", is_team: bool = False
    ) -> str:
        stage_label = "F-DC-124 (propuesta)" if fdc_type == FdcType.FDC_124 else "F-DC-125 (informe final)"
        address = f"el equipo ({student_name})" if is_team else student_name
        return (
            f"Actúa como un docente jurado real de las UTS dialogando con {address} sobre su {stage_label}: "
            "tono cercano, respetuoso, fluido y formativo (no fiscalizador ni adversarial). "
            "Formula 4 preguntas base abiertas, claras y directas sobre el contenido real del documento para que "
            f"{student_name} exponga y defienda su trabajo con naturalidad, sin convertir las preguntas base en ataques."
        )

    def build_turn_evaluation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante", is_team: bool = False
    ) -> str:
        stage_rules = resolve_defense_stage_policy(fdc_type).build_evaluation_stage_rules()
        return (
            f"Evalúa con objetividad, criterio formativo y calidez académica la intervención de {student_name}. "
            f"{stage_rules} "
            "Usa focos_aclaracion_apoyo únicamente como contexto auxiliar para proponer una contrapregunta puntual y "
            "constructiva solo si la respuesta fue muy vaga, incompleta o contradictoria frente a su propio documento (nota < 3.5). "
            "Redacta una transición humana breve y cordial reaccionando a lo dicho antes de avanzar."
            f"{_team_eval_note(student_name, is_team)}"
        )


class RigorousTechnicalJuryStrategy(JuryProfileStrategy):
    """Jurado técnico riguroso centrado en riesgos, supuestos y precisión respetando la etapa."""

    @property
    def profile(self) -> JuryProfile:
        return JuryProfile.TECNICO_RIGUROSO

    @property
    def name(self) -> str:
        return "RigorousTechnicalJuryStrategy"

    @property
    def follow_up_score_threshold(self) -> float:
        return 4.2

    @property
    def include_gaps_in_base_questions(self) -> bool:
        return True

    def build_question_generation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante", is_team: bool = False
    ) -> str:
        stage_label = "F-DC-124 (propuesta técnica)" if fdc_type == FdcType.FDC_124 else "F-DC-125 (informe final técnico)"
        address = f"el equipo ({student_name})" if is_team else student_name
        return (
            f"Actúa como jurado técnico riguroso pero respetuoso y dialogante de las UTS conversando con {address} "
            f"sobre su {stage_label}. Respeta estrictamente la etapa del documento, pero profundiza en riesgos técnicos, "
            "supuestos de diseño y focos críticos presentes en vacios_detectados."
        )

    def build_turn_evaluation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante", is_team: bool = False
    ) -> str:
        stage_rules = resolve_defense_stage_policy(fdc_type).build_evaluation_stage_rules()
        return (
            f"Contrasta con rigor técnico y claridad conceptual la respuesta de {student_name} frente a su documento. "
            f"{stage_rules} "
            "Penaliza respuestas genéricas sin sustento en el documento o en ingeniería, reconoce brevemente lo acertado "
            "en la transición humana y solicita aclaración técnica directa si la nota es inferior a 4.2."
            f"{_team_eval_note(student_name, is_team)}"
        )
