"""Entidades puras y cálculo ponderado de la rúbrica institucional UTS."""
from dataclasses import dataclass

from app.domain.entities.defense_enums import Verdict


@dataclass(frozen=True)
class RubricCriterion:
    """Criterio individual de evaluación con peso porcentual."""

    code: str
    label: str
    weight: float
    descriptor: str


@dataclass(frozen=True)
class RubricDefinition:
    """Rúbrica institucional parametrizada para sustentación de grado."""

    name: str
    period: str
    criteria: list[RubricCriterion]


def compute_weighted_score(scores_by_code: dict[str, float], rubric: RubricDefinition) -> float:
    """Calcula la nota ponderada (0.0 a 5.0) según pesos de la rúbrica."""
    total = 0.0
    for criterion in rubric.criteria:
        raw = float(scores_by_code.get(criterion.code, 0.0))
        clamped = max(0.0, min(5.0, raw))
        total += clamped * criterion.weight
    return round(total, 2)


def resolve_uts_verdict(score: float) -> Verdict:
    """Asigna concepto UTS: >=3.0 APROBADO, >1.0 y <3.0 APLAZADO, <=1.0 NO_APROBADO."""
    if score >= 3.0:
        return Verdict.APROBADO
    if score > 1.0:
        return Verdict.APLAZADO
    return Verdict.NO_APROBADO
