"""Factory Method para instanciar estrategias de análisis FDC."""
from app.domain.entities.fdc_document import FdcType, Modality
from app.domain.exceptions.fdc_exceptions import UnsupportedFdcTypeError
from app.domain.strategies.fdc_124_proposal_strategy import Fdc124ProposalStrategy
from app.domain.strategies.fdc_125_final_report_strategy import Fdc125FinalReportStrategy
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy

_STRATEGY_REGISTRY: dict[FdcType, type[FdcAnalysisStrategy]] = {
    FdcType.FDC_124: Fdc124ProposalStrategy,
    FdcType.FDC_125: Fdc125FinalReportStrategy,
}


class FdcStrategyFactory:
    """Fábrica declarativa de estrategias según tipo FDC y modalidad."""

    @staticmethod
    def create(fdc_type: FdcType | str, modality: Modality | None = None) -> FdcAnalysisStrategy:
        """Crea la estrategia correspondiente o lanza UnsupportedFdcTypeError."""
        try:
            resolved_type = fdc_type if isinstance(fdc_type, FdcType) else FdcType(fdc_type)
        except ValueError as exc:
            raise UnsupportedFdcTypeError(
                f"Tipo de formato FDC no soportado: '{fdc_type}'.",
                context={"fdc_type": str(fdc_type)},
            ) from exc

        strategy_cls = _STRATEGY_REGISTRY.get(resolved_type)
        if strategy_cls is None:
            raise UnsupportedFdcTypeError(
                f"No existe estrategia registrada para '{resolved_type}'.",
                context={"fdc_type": str(resolved_type)},
            )
        return strategy_cls(modality=modality)
