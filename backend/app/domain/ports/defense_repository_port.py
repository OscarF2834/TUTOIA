"""Puerto de persistencia para sesiones y turnos de sustentación."""
from typing import Protocol
from uuid import UUID

from app.domain.entities.defense_session import DefenseSession, DefenseTurn


class DefenseSessionRepositoryPort(Protocol):
    """Contrato de persistencia para DefenseSession y DefenseTurn."""

    def add_session(self, session: DefenseSession) -> None:
        """Inserta una nueva sesión de sustentación."""

    def update_session(self, session: DefenseSession) -> None:
        """Actualiza el estado y avance de una sesión existente."""

    def get_session(self, session_id: UUID) -> DefenseSession | None:
        """Recupera una sesión por su identificador."""

    def add_turn(self, turn: DefenseTurn) -> None:
        """Agrega un turno evaluado a la sesión."""

    def list_turns(self, session_id: UUID) -> list[DefenseTurn]:
        """Lista todos los turnos de una sesión ordenados por turn_number."""
