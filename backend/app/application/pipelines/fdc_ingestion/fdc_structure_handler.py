"""Eslabón 4: Validación estructural diferenciada para FDC-124 vs. FDC-125."""
import unicodedata

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.domain.exceptions.fdc_exceptions import InvalidFdcStructureError


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(without_marks.lower().split())


class FdcStructureHandler(IngestionHandler):
    """Verifica secciones mínimas oficiales según la Strategy (FDC-124 o FDC-125)."""

    def _process(self, ctx: FdcIngestionContext) -> None:
        normalized = _normalize_text(ctx.extracted_text)
        missing: list[str] = []
        for section, synonyms in ctx.strategy.required_sections.items():
            if not any(synonym in normalized for synonym in synonyms):
                missing.append(section)

        if missing:
            missing_sorted = sorted(missing)
            fdc_type = ctx.strategy.fdc_type.value
            raise InvalidFdcStructureError(
                message=(
                    f"El documento no cumple la estructura mínima requerida para {fdc_type}. "
                    f"Secciones faltantes: {', '.join(missing_sorted)}."
                ),
                context={"missing_sections": missing_sorted, "fdc_type": fdc_type},
            )
