"""Adaptador que carga la rúbrica institucional desde app/data/rubrica_uts.json."""
import json
from pathlib import Path

from app.domain.entities.rubric import RubricCriterion, RubricDefinition


class JsonRubricProviderAdapter:
    """Implementa RubricProviderPort leyendo el archivo JSON institucional UTS."""

    def __init__(self, rubric_path: Path) -> None:
        self._rubric_path = rubric_path
        self._cached: RubricDefinition | None = None

    def get_rubric(self) -> RubricDefinition:
        """Retorna la rúbrica institucional UTS cargada y cacheada."""
        if self._cached is None:
            payload = json.loads(self._rubric_path.read_text(encoding="utf-8"))
            criteria = [
                RubricCriterion(
                    code=item["codigo"],
                    label=item["etiqueta"],
                    weight=float(item["peso"]),
                    descriptor=item["descriptor"],
                )
                for item in payload["criterios"]
            ]
            self._cached = RubricDefinition(
                name=payload["nombre"],
                period=str(payload["periodo"]),
                criteria=criteria,
            )
        return self._cached
