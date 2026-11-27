"""Registro central de modelos ORM para Alembic y create_all."""
from app.infrastructure.db.models.defense_session_model import DefenseSessionModel
from app.infrastructure.db.models.defense_turn_model import DefenseTurnModel
from app.infrastructure.db.models.fdc_analysis_model import FdcAnalysisModel
from app.infrastructure.db.models.fdc_document_model import FdcDocumentModel
from app.infrastructure.db.models.project_model import ProjectModel

__all__ = [
    "ProjectModel",
    "FdcDocumentModel",
    "FdcAnalysisModel",
    "DefenseSessionModel",
    "DefenseTurnModel",
]
