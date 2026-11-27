"""Patrón Strategy para perfiles de jurado y política de contrapregunta."""
from abc import ABC, abstractmethod

from app.domain.entities.defense_enums import JuryProfile
from app.domain.entities.fdc_document import FdcType


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

    @abstractmethod
    def build_question_generation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante"
    ) -> str:
        """Directrices para generar las 4 preguntas base según formato y jurado."""

    @abstractmethod
    def build_turn_evaluation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante"
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
    """Jurado institucional cercano, dialogante y equilibrado conforme a la rúbrica UTS."""

    @property
    def profile(self) -> JuryProfile:
        return JuryProfile.ESTANDAR_UTS

    @property
    def name(self) -> str:
        return "StandardUtsJuryStrategy"

    @property
    def follow_up_score_threshold(self) -> float:
        return 3.5

    def build_question_generation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante"
    ) -> str:
        scope = (
            "propuesta de trabajo de grado F-DC-124 (descripción del problema, justificación, objetivos con plan de actividades y resultados esperados)"
            if fdc_type == FdcType.FDC_124
            else "informe final F-DC-125 (planteamiento del problema, justificación, objetivos con metodología ejecutada y resultados/conclusiones)"
        )
        return (
            f"Eres un jurado humano de las UTS cercano, respetuoso y conversacional dialogando con {student_name} sobre su {scope}. "
            "Habla de tú natural y fluido, como en una sustentación real de sala universitaria, evitando preguntas rígidas tipo cuestionario."
        )

    def build_turn_evaluation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante"
    ) -> str:
        return (
            f"Evalúa con objetividad y calidez académica la respuesta de {student_name} contra la rúbrica UTS y el documento {fdc_type.value}. "
            "Redacta una transición humana breve que reaccione directamente a lo que respondió antes de avanzar, "
            "y si omite puntos clave o la nota baja de 3.5 formula una contrapregunta conversacional."
        )


class RigorousTechnicalJuryStrategy(JuryProfileStrategy):
    """Jurado técnico riguroso pero dialogante, centrado en método, decisiones y evidencia."""

    @property
    def profile(self) -> JuryProfile:
        return JuryProfile.TECNICO_RIGUROSO

    @property
    def name(self) -> str:
        return "RigorousTechnicalJuryStrategy"

    @property
    def follow_up_score_threshold(self) -> float:
        return 4.2

    def build_question_generation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante"
    ) -> str:
        scope = (
            "propuesta técnica F-DC-124 (problema, justificación técnica, coherencia objetivos-plan y métricas esperadas)"
            if fdc_type == FdcType.FDC_124
            else "informe final F-DC-125 (decisiones de ingeniería, metodología aplicada, métricas y resultados reales)"
        )
        return (
            f"Eres un jurado técnico riguroso pero respetuoso y dialogante de las UTS conversando con {student_name} sobre su {scope}. "
            "Combina cercanía humana (tratándolo por su nombre) con profundidad técnica sobre decisiones, supuestos y vacíos del FDC."
        )

    def build_turn_evaluation_guidance(
        self, fdc_type: FdcType, student_name: str = "estudiante"
    ) -> str:
        return (
            f"Contrasta con rigor lo dicho por {student_name} frente al contenido real de su {fdc_type.value}. "
            "Penaliza respuestas genéricas sin respaldo en el proyecto, reconoce brevemente lo acertado en una transición humana "
            "y pide aclaración técnica directa en lenguaje natural si la nota es inferior a 4.2."
        )
