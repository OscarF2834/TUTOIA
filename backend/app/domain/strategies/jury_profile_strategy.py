"""Patrón Strategy para perfiles de jurado y política de contrapregunta."""
from abc import ABC, abstractmethod

from app.domain.entities.defense_enums import JuryProfile
from app.domain.entities.fdc_document import FdcType


class JuryProfileStrategy(ABC):
    """Define rigor de evaluación y umbral de disparo de contrapregunta."""

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
    def build_question_generation_guidance(self, fdc_type: FdcType) -> str:
        """Directrices para generar las 4 preguntas base según formato y jurado."""

    @abstractmethod
    def build_turn_evaluation_guidance(self, fdc_type: FdcType) -> str:
        """Directrices para evaluar la respuesta del estudiante."""

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
    """Jurado institucional equilibrado conforme a la rúbrica UTS."""

    @property
    def profile(self) -> JuryProfile:
        return JuryProfile.ESTANDAR_UTS

    @property
    def name(self) -> str:
        return "StandardUtsJuryStrategy"

    @property
    def follow_up_score_threshold(self) -> float:
        return 3.5

    def build_question_generation_guidance(self, fdc_type: FdcType) -> str:
        scope = (
            "propuesta de grado F-DC-124 (problema, fundamentación, plan de actividades y resultados esperados)"
            if fdc_type == FdcType.FDC_124
            else "informe final F-DC-125 (problema, fundamentación teórica, metodología ejecutada y resultados/validación)"
        )
        return (
            f"Actúa como jurado institucional UTS equilibrado y formativo sobre {scope}. "
            "Formula preguntas claras, directas y verificables que permitan al sustentante demostrar dominio."
        )

    def build_turn_evaluation_guidance(self, fdc_type: FdcType) -> str:
        return (
            f"Evalúa de forma justa y objetiva contra la rúbrica UTS para {fdc_type.value}. "
            "Si la respuesta omite evidencia clave o queda por debajo de 3.5, recomienda una contrapregunta breve."
        )


class RigorousTechnicalJuryStrategy(JuryProfileStrategy):
    """Jurado técnico riguroso centrado en ingeniería, método y validación empírica."""

    @property
    def profile(self) -> JuryProfile:
        return JuryProfile.TECNICO_RIGUROSO

    @property
    def name(self) -> str:
        return "RigorousTechnicalJuryStrategy"

    @property
    def follow_up_score_threshold(self) -> float:
        return 4.2

    def build_question_generation_guidance(self, fdc_type: FdcType) -> str:
        scope = (
            "propuesta técnica F-DC-124 (factibilidad, arquitectura/diseño planteado, riesgos y plan)"
            if fdc_type == FdcType.FDC_124
            else "informe final F-DC-125 (decisiones técnicas, métricas de validación, límites y resultados)"
        )
        return (
            f"Actúa como jurado técnico riguroso de ingeniería sobre {scope}. "
            "Prioriza cuestionamientos profundos sobre decisiones técnicas, métricas, supuestos y vacíos críticos."
        )

    def build_turn_evaluation_guidance(self, fdc_type: FdcType) -> str:
        return (
            f"Exige precisión conceptual, técnica y metodológica para {fdc_type.value}. "
            "Penaliza respuestas genéricas o sin respaldo en evidencia del documento y solicita aclaración si nota < 4.2."
        )
