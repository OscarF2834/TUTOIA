"""Pruebas unitarias de JuryStrategyFactory, JuryProfileStrategy y rúbrica UTS."""
import pytest

from app.domain.entities.defense_enums import JuryProfile, Verdict
from app.domain.entities.fdc_document import FdcType
from app.domain.entities.rubric import RubricCriterion, RubricDefinition, compute_weighted_score, resolve_uts_verdict
from app.domain.exceptions.defense_exceptions import UnsupportedJuryProfileError
from app.domain.factories.jury_strategy_factory import JuryStrategyFactory
from app.domain.strategies.jury_profile_strategy import (
    RigorousTechnicalJuryStrategy,
    StandardUtsJuryStrategy,
)


def test_jury_factory_resolves_profiles_and_rejects_unknown() -> None:
    standard = JuryStrategyFactory.create(JuryProfile.ESTANDAR_UTS)
    rigorous = JuryStrategyFactory.create("TECNICO_RIGUROSO")
    assert isinstance(standard, StandardUtsJuryStrategy)
    assert isinstance(rigorous, RigorousTechnicalJuryStrategy)
    assert rigorous.follow_up_score_threshold > standard.follow_up_score_threshold
    assert "F-DC-124" in standard.build_question_generation_guidance(FdcType.FDC_124)

    with pytest.raises(UnsupportedJuryProfileError):
        JuryStrategyFactory.create("JURADO_INEXISTENTE")


def test_strict_limit_of_at_most_one_follow_up_per_base_question() -> None:
    rigorous = JuryStrategyFactory.create(JuryProfile.TECNICO_RIGUROSO)

    assert rigorous.should_trigger_follow_up(
        already_followed_up=False,
        weighted_score=2.0,
        ai_recommends_follow_up=True,
        follow_up_text="¿Qué métrica respalda ese resultado?",
    ) is True

    assert rigorous.should_trigger_follow_up(
        already_followed_up=True,
        weighted_score=1.0,
        ai_recommends_follow_up=True,
        follow_up_text="Segunda contrapregunta que debe bloquearse.",
    ) is False

    assert rigorous.should_trigger_follow_up(
        already_followed_up=False,
        weighted_score=2.0,
        ai_recommends_follow_up=True,
        follow_up_text="   ",
    ) is False


def test_rubric_weighted_score_and_uts_verdict_thresholds() -> None:
    rubric = RubricDefinition(
        name="UTS",
        period="2026",
        criteria=[
            RubricCriterion("pertinencia", "Pertinencia", 0.30, ""),
            RubricCriterion("coherencia", "Coherencia", 0.25, ""),
            RubricCriterion("fundamentacion", "Fundamentación", 0.25, ""),
            RubricCriterion("metodologia", "Metodología", 0.20, ""),
        ],
    )
    score = compute_weighted_score(
        {"pertinencia": 4.0, "coherencia": 4.0, "fundamentacion": 3.0, "metodologia": 4.5},
        rubric,
    )
    assert score == 3.85
    assert resolve_uts_verdict(3.0) == Verdict.APROBADO
    assert resolve_uts_verdict(2.99) == Verdict.APLAZADO
    assert resolve_uts_verdict(1.0) == Verdict.NO_APROBADO
