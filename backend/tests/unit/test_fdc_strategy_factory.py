"""Pruebas unitarias de FdcStrategyFactory y estrategias FDC."""
import pytest

from app.domain.entities.fdc_document import FdcType, Modality
from app.domain.exceptions.fdc_exceptions import UnsupportedFdcTypeError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from app.domain.strategies.fdc_124_proposal_strategy import Fdc124ProposalStrategy
from app.domain.strategies.fdc_125_final_report_strategy import Fdc125FinalReportStrategy


def test_factory_creates_expected_strategy_classes() -> None:
    s124 = FdcStrategyFactory.create(FdcType.FDC_124)
    s125 = FdcStrategyFactory.create(FdcType.FDC_125)
    assert isinstance(s124, Fdc124ProposalStrategy)
    assert isinstance(s125, Fdc125FinalReportStrategy)
    assert set(s124.required_sections.keys()) != set(s125.required_sections.keys())


def test_factory_propagates_modality_into_strategy_guidance() -> None:
    strategy = FdcStrategyFactory.create(FdcType.FDC_124, modality=Modality.INVESTIGACION)
    assert strategy.modality == Modality.INVESTIGACION
    assert "hipótesis" in strategy.build_system_instruction()


def test_factory_rejects_unknown_fdc_type() -> None:
    with pytest.raises(UnsupportedFdcTypeError):
        FdcStrategyFactory.create("FDC_999")
