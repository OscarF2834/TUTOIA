"""Pruebas unitarias de Fdc124ProposalStrategy, JuryStrategyFactory, JuryProfileStrategy y rúbrica UTS."""
import pytest

from app.domain.entities.defense_enums import JuryProfile, Verdict
from app.domain.entities.fdc_document import FdcType
from app.domain.entities.rubric import RubricCriterion, RubricDefinition, compute_weighted_score, resolve_uts_verdict
from app.domain.exceptions.defense_exceptions import UnsupportedJuryProfileError
from app.domain.factories.jury_strategy_factory import JuryStrategyFactory
from app.domain.strategies.defense_stage_policy import resolve_defense_stage_policy
from app.domain.strategies.fdc_124_proposal_strategy import Fdc124ProposalStrategy
from app.domain.strategies.jury_profile_strategy import (
    RigorousTechnicalJuryStrategy,
    StandardUtsJuryStrategy,
)


def test_fdc_124_proposal_strategy_enforces_uts_grid_without_execution_penalty() -> None:
    strategy = Fdc124ProposalStrategy()
    sys_inst = strategy.build_system_instruction()
    prompt = strategy.build_analysis_prompt()
    assert "Rejilla de Evaluación de Propuesta UTS" in sys_inst
    assert "PROHIBIDO penalizar" in sys_inst
    assert "software implementado" in sys_inst
    assert "sin exigir resultados ni pruebas ya ejecutadas" in prompt


def test_jury_factory_resolves_profiles_and_stage_separation() -> None:
    standard = JuryStrategyFactory.create(JuryProfile.ESTANDAR_UTS)
    rigorous = JuryStrategyFactory.create("TECNICO_RIGUROSO")
    assert isinstance(standard, StandardUtsJuryStrategy)
    assert isinstance(rigorous, RigorousTechnicalJuryStrategy)
    assert rigorous.follow_up_score_threshold > standard.follow_up_score_threshold
    assert standard.include_gaps_in_base_questions is False
    assert rigorous.include_gaps_in_base_questions is True

    guidance_124 = standard.build_question_generation_guidance(FdcType.FDC_124, "Pedro")
    assert "F-DC-124" in guidance_124
    assert "no fiscalizador" in guidance_124

    eval_124 = standard.build_turn_evaluation_guidance(FdcType.FDC_124, "Pedro")
    assert "NUNCA bajes la calificación porque el estudiante hable en futuro" in eval_124

    arc_124 = resolve_defense_stage_policy(FdcType.FDC_124).build_question_arc("Pedro", "TutoIA")
    assert "ENFOQUE PROSPECTIVO/FUTURO" in arc_124
    assert "PROHIBIDO preguntar como si el sistema ya estuviera construido" in arc_124

    arc_125 = resolve_defense_stage_policy(FdcType.FDC_125).build_question_arc("Pedro", "TutoIA")
    assert "ENFOQUE RETROSPECTIVO/PASADO" in arc_125
    assert "qué resultados concretos arrojaron las pruebas" in arc_125

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
