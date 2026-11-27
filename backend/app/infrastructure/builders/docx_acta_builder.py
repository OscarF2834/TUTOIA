"""Constructor concreto DOCX editable del Acta Oficial usando python-docx."""
import io

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

from app.domain.builders.acta_report_data import ActaReportData
from app.domain.builders.defense_acta_builder import DefenseActaBuilder

_UTS_HEX = "047857"
_SLATE_BG = "F1F5F9"
_SLATE_DARK = RGBColor(0x0F, 0x17, 0x2A)
_SLATE_MUTED = RGBColor(0x47, 0x55, 0x69)
_UTS_RGB = RGBColor(0x04, 0x78, 0x57)


def _shade_cell(cell, hex_color: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _apply_table_borders(table, hex_color: str = "CBD5E1") -> None:
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        "</w:tblBorders>"
    )
    table._tbl.tblPr.append(borders)


def _set_cell_text(cell, text: str, bold: bool = False, color: RGBColor = _SLATE_DARK, size: int = 9) -> None:
    cell.text = ""
    run = cell.paragraphs[0].add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = color


class DocxActaBuilder(DefenseActaBuilder):
    """Construye el Acta UTS editable en Microsoft Word (.docx)."""

    def __init__(self) -> None:
        self._doc: Document | None = None

    def reset(self) -> None:
        doc = Document()
        for section in doc.sections:
            section.top_margin = Inches(0.65)
            section.bottom_margin = Inches(0.65)
            section.left_margin = Inches(0.7)
            section.right_margin = Inches(0.7)
        normal = doc.styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(10)
        self._doc = doc

    def add_institutional_header(self, data: ActaReportData) -> None:
        doc = self._require_doc()
        banner = doc.add_table(rows=1, cols=1)
        cell = banner.cell(0, 0)
        _shade_cell(cell, _UTS_HEX)
        p = cell.paragraphs[0]
        r1 = p.add_run("UNIDADES TECNOLÓGICAS DE SANTANDER (UTS)\n")
        r1.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = RGBColor(0xD1, 0xFA, 0xE5)
        r2 = p.add_run("ACTA PRELIMINAR DE SUSTENTACIÓN DE TRABAJO DE GRADO · TutoIA\n")
        r2.bold = True
        r2.font.size = Pt(13)
        r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r3 = p.add_run(f"Acta ID: {data.session_id[:8].upper()}  ·  Cierre: {data.completed_at}  ·  Emisión: {data.generated_at}")
        r3.font.size = Pt(8.5)
        r3.font.color.rgb = RGBColor(0xEC, 0xFD, 0xF5)
        doc.add_paragraph()

    def add_project_metadata(self, data: ActaReportData) -> None:
        doc = self._require_doc()
        self._add_section_heading("1. Identificación del Proyecto y Sustentantes")
        authors_text = ", ".join(data.authors) if data.authors else "No registrado"
        items = [
            ("Título del proyecto", data.project_title),
            ("Formato evaluado", data.fdc_type_label),
            ("Programa / Modalidad", f"{data.academic_program} · {data.modality_label}"),
            ("Sustentante(s)", authors_text),
            ("Director(a)", data.director_name),
            ("Perfil jurado AURA", f"{data.jury_profile_label} · {data.rubric_name}"),
        ]
        table = doc.add_table(rows=len(items), cols=2)
        _apply_table_borders(table)
        for idx, (label, val) in enumerate(items):
            _shade_cell(table.cell(idx, 0), _SLATE_BG)
            _set_cell_text(table.cell(idx, 0), label, bold=True)
            _set_cell_text(table.cell(idx, 1), val)
        doc.add_paragraph()

    def add_rubric_evaluation(self, data: ActaReportData) -> None:
        doc = self._require_doc()
        self._add_section_heading("2. Evaluación Cuantitativa por Rúbrica Institucional UTS")
        summary_p = doc.add_paragraph()
        run = summary_p.add_run(
            f"Calificación consolidada preliminar: {data.overall_score:.2f} / 5.00   |   Concepto preliminar: {data.verdict}"
        )
        run.bold = True
        run.font.color.rgb = _UTS_RGB

        table = doc.add_table(rows=len(data.criteria_rows) + 1, cols=4)
        _apply_table_borders(table)
        headers = ("Criterio institucional", "Peso (%)", "Promedio (0–5)", "Aporte ponderado")
        for col_idx, title in enumerate(headers):
            cell = table.cell(0, col_idx)
            _shade_cell(cell, _UTS_HEX)
            _set_cell_text(cell, title, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))

        for row_idx, row in enumerate(data.criteria_rows, start=1):
            _set_cell_text(table.cell(row_idx, 0), row.label)
            _set_cell_text(table.cell(row_idx, 1), f"{row.weight_percent} %")
            _set_cell_text(table.cell(row_idx, 2), f"{row.average_score:.2f}", bold=True)
            _set_cell_text(table.cell(row_idx, 3), f"{row.weighted_contribution:.2f}", bold=True)
        doc.add_paragraph()

    def add_qualitative_feedback(self, data: ActaReportData) -> None:
        doc = self._require_doc()
        self._add_section_heading("3. Síntesis Cualitativa y Retroalimentación")
        doc.add_paragraph(data.closing_message)

        table = doc.add_table(rows=2, cols=2)
        _apply_table_borders(table)
        _shade_cell(table.cell(0, 0), "334155")
        _shade_cell(table.cell(0, 1), "334155")
        _set_cell_text(table.cell(0, 0), "Fortalezas observadas", bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        _set_cell_text(table.cell(0, 1), "Oportunidades de mejora", bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        _set_cell_text(table.cell(1, 0), "\n".join(f"• {s}" for s in data.strengths) or "• Sin observaciones.")
        _set_cell_text(table.cell(1, 1), "\n".join(f"• {i}" for i in data.improvements) or "• Sin observaciones.")
        doc.add_paragraph()

    def add_defense_transcript(self, data: ActaReportData) -> None:
        doc = self._require_doc()
        self._add_section_heading("4. Bitácora Cronológica de Sustentación Oral")
        table = doc.add_table(rows=len(data.turns) + 1, cols=4)
        _apply_table_borders(table)
        headers = ("Turno", "Pregunta formulada por AURA", "Transcripción del sustentante", "Nota y feedback")
        for col_idx, title in enumerate(headers):
            cell = table.cell(0, col_idx)
            _shade_cell(cell, _UTS_HEX)
            _set_cell_text(cell, title, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))

        for row_idx, turn in enumerate(data.turns, start=1):
            label = f"#{turn.turn_number} ({turn.thematic_axis})" + (" [Contrapregunta]" if turn.is_follow_up else "")
            _set_cell_text(table.cell(row_idx, 0), label, size=8.5, color=_SLATE_MUTED)
            _set_cell_text(table.cell(row_idx, 1), turn.aura_question, size=8.5)
            _set_cell_text(table.cell(row_idx, 2), f"[{turn.input_mode}] {turn.student_transcript}", size=8.5)
            _set_cell_text(table.cell(row_idx, 3), f"Nota: {turn.weighted_score:.2f}/5.0\n{turn.turn_feedback}", size=8.5)
        doc.add_paragraph()

    def add_hitl_and_signatures(self, data: ActaReportData) -> None:
        doc = self._require_doc()
        self._add_section_heading("5. Supervisión Humana (Human-in-the-Loop) y Firmas")
        notice = doc.add_table(rows=1, cols=1)
        _apply_table_borders(notice)
        _shade_cell(notice.cell(0, 0), _SLATE_BG)
        _set_cell_text(notice.cell(0, 0), data.human_in_the_loop_notice, size=9)
        doc.add_paragraph()

        signs = doc.add_table(rows=2, cols=3)
        for col_idx, label in enumerate(("Jurado Docente 1 · UTS", "Jurado Docente 2 · UTS", "Sustentante(s)")):
            _set_cell_text(signs.cell(0, col_idx), "\n___________________________")
            _set_cell_text(signs.cell(1, col_idx), label, bold=True, size=9)

    def build(self) -> bytes:
        doc = self._require_doc()
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    def _add_section_heading(self, title: str) -> None:
        p = self._require_doc().add_paragraph()
        run = p.add_run(title)
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = _UTS_RGB

    def _require_doc(self) -> Document:
        if self._doc is None:
            raise RuntimeError("Debe invocar reset() antes de construir secciones del acta.")
        return self._doc
