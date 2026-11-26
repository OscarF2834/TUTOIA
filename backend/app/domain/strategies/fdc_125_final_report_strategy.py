"""Estrategia concreta para Informe Final de Trabajo de Grado (F-DC-125)."""
from app.domain.entities.fdc_document import FdcType
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy


class Fdc125FinalReportStrategy(FdcAnalysisStrategy):
    """Reglas estructurales y criterios de análisis para formato F-DC-125."""

    @property
    def name(self) -> str:
        return "Fdc125FinalReportStrategy"

    @property
    def fdc_type(self) -> FdcType:
        return FdcType.FDC_125

    @property
    def required_sections(self) -> dict[str, tuple[str, ...]]:
        return {
            "problema": (
                "planteamiento del problema",
                "descripcion del problema",
                "formulacion del problema",
                "descripcion del trabajo de investigacion",
                "problema",
            ),
            "objetivos": (
                "objetivo general",
                "objetivos especificos",
                "objetivos",
            ),
            "diseno_o_metodologia": (
                "diseno de la investigacion",
                "desarrollo del trabajo de grado",
                "metodologia",
                "diseno metodologico",
                "marco metodologico",
            ),
            "resultados": ("resultados",),
            "conclusiones": ("conclusiones",),
        }

    def build_system_instruction(self) -> str:
        return (
            "Eres un jurado evaluador senior de las Unidades Tecnológicas de Santander (UTS). "
            "Analizas informes finales de trabajo de grado en formato oficial F-DC-125. "
            "Usa únicamente evidencia real del proyecto diligenciado; está prohibido inventar cifras, autores "
            "o conclusiones. Ignora estrictamente placeholders y secciones instructivas de la plantilla UTS: "
            "Nota de Aceptación en blanco, textos guía de Dedicatoria/Agradecimientos, encabezados placeholder "
            "('Título al que optan los autores', 'Ciudad y fecha'), Instructivo General ('Apreciado Estudiante...'), "
            "AYUDAS PARA LA PRESENTACIÓN DEL DOCUMENTO, Figura 1 de ejemplo y Tabla 1 de ejemplo en Java. "
            f"{self.modality_guidance()}"
        )

    def build_analysis_prompt(self) -> str:
        return (
            "Analiza exhaustivamente este informe final F-DC-125 de las UTS. Reconoce la estructura oficial: "
            "Portada/Contraportada (título, modalidad, autores y CC, director, grupo de investigación, facultad/"
            "programa), Resumen Ejecutivo, Introducción, Planteamiento del Problema (involucrados, causas, efectos, "
            "pregunta), Justificación, Objetivos, Estado del Arte, Marco Referencial, Diseño de la Investigación, "
            "Desarrollo del Trabajo de Grado, Resultados, Conclusiones, Recomendaciones y Referencias. "
            "Extrae metodología, fases e instrumentos desde Diseño de la Investigación, Desarrollo del Trabajo de "
            "Grado, Resumen Ejecutivo e Introducción (en Emprendimiento puede pasar directo a Desarrollo). "
            "ALERTA CRÍTICA DE PLANTILLA: si capítulos como Marco Referencial, Diseño de la Investigación, "
            "Desarrollo del Trabajo de Grado, Resultados o Conclusiones contienen únicamente texto guía genérico "
            "de la plantilla UTS (ej. 'En esta sección se detallan...', 'Las conclusiones deben indicar...') sin "
            "contenido propio del proyecto, NO los reportes como evidencia real: califica esa dimensión como "
            "DEFICIENTE o PARCIAL en coherence_findings y regístralo como vacío de severidad ALTA en "
            "detected_gaps_for_defense para indagarlo en la sustentación."
        )
