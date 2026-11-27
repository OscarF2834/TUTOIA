"""Constructor concreto PDF del Acta Oficial usando ReportLab."""
import io

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.domain.builders.acta_report_data import ActaReportData
from app.domain.builders.defense_acta_builder import DefenseActaBuilder
from app.infrastructure.builders.pdf_acta_styles import (
    AMBER_SOFT,
    BASE_CELL_PADDING,
    ROSE_SOFT,
    SLATE_100,
    SLATE_200,
    SLATE_700,
    UTS_EMERALD,
    UTS_EMERALD_BORDER,
    UTS_EMERALD_SOFT,
    WHITE,
    build_acta_styles,
    draw_page_footer,
    safe_xml,
)

_CONTENT_WIDTH = 528.0


class PdfActaBuilder(DefenseActaBuilder):
    """Construye un documento PDF institucional Carta limpio sin dependencias nativas."""

    def __init__(self) -> None:
        self._styles = build_acta_styles()
        self._elements: list = []

    def reset(self) -> None:
        self._elements = []

    def add_institutional_header(self, data: ActaReportData) -> None:
        banner = Table(
            [
                [Paragraph("UNIDADES TECNOLÓGICAS DE SANTANDER (UTS)", self._styles["header_sub"])],
                [Paragraph("ACTA PRELIMINAR DE SUSTENTACIÓN DE TRABAJO DE GRADO · TutoIA", self._styles["header_title"])],
                [
                    Paragraph(
                        safe_xml(f"Acta ID: {data.session_id[:8].upper()}  ·  Cierre: {data.completed_at}  ·  Emisión: {data.generated_at}"),
                        self._styles["header_sub"],
                    )
                ],
            ],
            colWidths=[_CONTENT_WIDTH],
        )
        banner.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), UTS_EMERALD),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (-1, -1), 3),
            ])
        )
        self._elements.extend([banner, Spacer(1, 10)])

    def add_project_metadata(self, data: ActaReportData) -> None:
        self._elements.append(Paragraph("1. Identificación del Proyecto y Sustentantes", self._styles["section"]))
        authors_text = ", ".join(data.authors) if data.authors else "No registrado"
        rows = [
            ("Título del proyecto", data.project_title),
            ("Formato evaluado", data.fdc_type_label),
            ("Programa / Modalidad", f"{data.academic_program} · {data.modality_label}"),
            ("Sustentante(s)", authors_text),
            ("Director(a)", data.director_name),
            ("Perfil jurado AURA", f"{data.jury_profile_label} · {data.rubric_name}"),
        ]
        table_rows = [
            [Paragraph(safe_xml(label), self._styles["body_bold"]), Paragraph(safe_xml(val), self._styles["body"])]
            for label, val in rows
        ]
        table = Table(table_rows, colWidths=[132, 396])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), SLATE_100), ("VALIGN", (0, 0), (-1, -1), "TOP"), *BASE_CELL_PADDING]))
        self._elements.extend([table, Spacer(1, 8)])

    def add_rubric_evaluation(self, data: ActaReportData) -> None:
        self._elements.append(Paragraph("2. Evaluación Cuantitativa por Rúbrica Institucional UTS", self._styles["section"]))
        verdict_bg = UTS_EMERALD_SOFT if data.verdict == "APROBADO" else AMBER_SOFT if data.verdict == "APLAZADO" else ROSE_SOFT
        summary_band = Table(
            [[
                Paragraph(safe_xml(f"Calificación consolidada preliminar: {data.overall_score:.2f} / 5.00"), self._styles["body_bold"]),
                Paragraph(safe_xml(f"Concepto preliminar: {data.verdict}"), self._styles["table_num"]),
            ]],
            colWidths=[320, 208],
        )
        summary_band.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), verdict_bg),
                ("BOX", (0, 0), (-1, -1), 0.75, UTS_EMERALD_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        header = [
            Paragraph("Criterio institucional", self._styles["table_header"]),
            Paragraph("Peso", self._styles["table_header"]),
            Paragraph("Promedio (0–5)", self._styles["table_header"]),
            Paragraph("Aporte ponderado", self._styles["table_header"]),
        ]
        body_rows = [
            [
                Paragraph(safe_xml(row.label), self._styles["table_cell"]),
                Paragraph(f"{row.weight_percent} %", self._styles["table_num"]),
                Paragraph(f"{row.average_score:.2f}", self._styles["table_num"]),
                Paragraph(f"{row.weighted_contribution:.2f}", self._styles["table_num"]),
            ]
            for row in data.criteria_rows
        ]
        rubric_table = Table([header, *body_rows], colWidths=[248, 70, 105, 105], repeatRows=1)
        rubric_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), UTS_EMERALD),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_100, WHITE]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                *BASE_CELL_PADDING,
            ])
        )
        self._elements.extend([summary_band, Spacer(1, 5), rubric_table, Spacer(1, 8)])

    def add_qualitative_feedback(self, data: ActaReportData) -> None:
        self._elements.append(Paragraph("3. Síntesis Cualitativa y Retroalimentación", self._styles["section"]))
        self._elements.extend([Paragraph(safe_xml(data.closing_message), self._styles["body"]), Spacer(1, 5)])
        strengths_html = "<br/>".join(f"• {safe_xml(s)}" for s in data.strengths) or "• Sin observaciones."
        improve_html = "<br/>".join(f"• {safe_xml(i)}" for i in data.improvements) or "• Sin observaciones."
        qual_table = Table(
            [
                [Paragraph("Fortalezas observadas", self._styles["table_header"]), Paragraph("Oportunidades de mejora", self._styles["table_header"])],
                [Paragraph(strengths_html, self._styles["table_cell"]), Paragraph(improve_html, self._styles["table_cell"])],
            ],
            colWidths=[264, 264],
        )
        qual_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), SLATE_700), ("VALIGN", (0, 0), (-1, -1), "TOP"), *BASE_CELL_PADDING]))
        self._elements.extend([qual_table, Spacer(1, 8)])

    def add_defense_transcript(self, data: ActaReportData) -> None:
        self._elements.append(Paragraph("4. Bitácora Cronológica de Sustentación Oral", self._styles["section"]))
        header = [
            Paragraph("Turno", self._styles["table_header"]),
            Paragraph("Pregunta formulada por AURA", self._styles["table_header"]),
            Paragraph("Transcripción del sustentante", self._styles["table_header"]),
            Paragraph("Nota y feedback", self._styles["table_header"]),
        ]
        rows = [
            [
                Paragraph(safe_xml(f"#{t.turn_number}\n({t.thematic_axis})" + ("\n[Contrapregunta]" if t.is_follow_up else "")), self._styles["small"]),
                Paragraph(safe_xml(t.aura_question), self._styles["table_cell"]),
                Paragraph(safe_xml(f"[{t.input_mode}] {t.student_transcript}"), self._styles["table_cell"]),
                Paragraph(safe_xml(f"Nota: {t.weighted_score:.2f}/5.0\n{t.turn_feedback}"), self._styles["table_cell"]),
            ]
            for t in data.turns
        ]
        transcript_table = Table([header, *rows], colWidths=[68, 155, 175, 130], repeatRows=1)
        transcript_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), UTS_EMERALD), ("VALIGN", (0, 0), (-1, -1), "TOP"), *BASE_CELL_PADDING]))
        self._elements.extend([transcript_table, Spacer(1, 10)])

    def add_hitl_and_signatures(self, data: ActaReportData) -> None:
        hitl_box = Table(
            [[Paragraph(safe_xml(f"5. Cláusula de Supervisión Humana (Human-in-the-Loop): {data.human_in_the_loop_notice}"), self._styles["body"])]],
            colWidths=[_CONTENT_WIDTH],
        )
        hitl_box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SLATE_100), ("BOX", (0, 0), (-1, -1), 0.75, SLATE_200), *BASE_CELL_PADDING]))
        sign_table = Table(
            [
                ["_______________________________", "_______________________________", "_______________________________"],
                [
                    Paragraph("Jurado Docente 1 · UTS", self._styles["sign_label"]),
                    Paragraph("Jurado Docente 2 · UTS", self._styles["sign_label"]),
                    Paragraph("Sustentante(s)", self._styles["sign_label"]),
                ],
            ],
            colWidths=[176, 176, 176],
        )
        sign_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, 0), 22)]))
        self._elements.append(KeepTogether([hitl_box, Spacer(1, 10), sign_table]))

    def build(self) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=LETTER,
            leftMargin=42,
            rightMargin=42,
            topMargin=42,
            bottomMargin=50,
            title="Acta Oficial de Sustentación TutoIA - UTS",
        )
        doc.build(self._elements, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
        return buffer.getvalue()
