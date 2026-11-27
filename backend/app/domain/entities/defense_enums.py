"""Objetos de valor e invariantes enumeradas de la sustentación."""
from enum import StrEnum


class DefenseStateStatus(StrEnum):
    """Estados oficiales de la máquina de estados de sustentación."""

    PREPARING = "PREPARING"
    AURA_SPEAKING = "AURA_SPEAKING"
    LISTENING_STUDENT = "LISTENING_STUDENT"
    EVALUATING_TURN = "EVALUATING_TURN"
    COMPLETED = "COMPLETED"


class JuryProfile(StrEnum):
    """Perfiles de rigor del jurado evaluador."""

    ESTANDAR_UTS = "ESTANDAR_UTS"
    TECNICO_RIGUROSO = "TECNICO_RIGUROSO"


class InputMode(StrEnum):
    """Canal de entrada utilizado por el estudiante en un turno."""

    AUDIO = "AUDIO"
    TEXT = "TEXT"


class Verdict(StrEnum):
    """Veredictos institucionales oficiales de sustentación UTS."""

    APROBADO = "APROBADO"
    APLAZADO = "APLAZADO"
    NO_APROBADO = "NO_APROBADO"
