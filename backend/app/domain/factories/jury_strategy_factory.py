"""Factory Method para instanciar estrategias de jurado de sustentación."""
from app.domain.entities.defense_enums import JuryProfile
from app.domain.exceptions.defense_exceptions import UnsupportedJuryProfileError
from app.domain.strategies.jury_profile_strategy import (
    JuryProfileStrategy,
    RigorousTechnicalJuryStrategy,
    StandardUtsJuryStrategy,
)

_JURY_REGISTRY: dict[JuryProfile, type[JuryProfileStrategy]] = {
    JuryProfile.ESTANDAR_UTS: StandardUtsJuryStrategy,
    JuryProfile.TECNICO_RIGUROSO: RigorousTechnicalJuryStrategy,
}


class JuryStrategyFactory:
    """Fábrica declarativa de estrategias por perfil de jurado."""

    @staticmethod
    def create(profile: JuryProfile | str) -> JuryProfileStrategy:
        """Crea la estrategia del perfil indicado o lanza UnsupportedJuryProfileError."""
        try:
            resolved = profile if isinstance(profile, JuryProfile) else JuryProfile(profile)
        except ValueError as exc:
            raise UnsupportedJuryProfileError(
                message=f"Perfil de jurado no soportado: '{profile}'.",
                context={"jury_profile": str(profile)},
            ) from exc

        strategy_cls = _JURY_REGISTRY.get(resolved)
        if strategy_cls is None:
            raise UnsupportedJuryProfileError(
                message=f"No hay estrategia registrada para el perfil '{resolved}'.",
                context={"jury_profile": str(resolved)},
            )
        return strategy_cls()
