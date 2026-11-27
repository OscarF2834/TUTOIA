"""Puerto proveedor de la rúbrica institucional de sustentación."""
from typing import Protocol

from app.domain.entities.rubric import RubricDefinition


class RubricProviderPort(Protocol):
    """Contrato para cargar la rúbrica ponderada vigente."""

    def get_rubric(self) -> RubricDefinition:
        """Retorna la definición de criterios, pesos y descriptores."""
