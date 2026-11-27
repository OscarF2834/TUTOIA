"""Estilos tipográficos, paleta UTS y utilidades XML para PdfActaBuilder."""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle

UTS_EMERALD = colors.HexColor("#047857")
UTS_EMERALD_SOFT = colors.HexColor("#ECFDF5")
UTS_EMERALD_BORDER = colors.HexColor("#A7F3D0")
SLATE_900 = colors.HexColor("#0F172A")
SLATE_700 = colors.HexColor("#334155")
SLATE_500 = colors.HexColor("#64748B")
SLATE_200 = colors.HexColor("#E2E8F0")
SLATE_100 = colors.HexColor("#F1F5F9")
AMBER_SOFT = colors.HexColor("#FFFBEB")
ROSE_SOFT = colors.HexColor("#FFF1F2")
WHITE = colors.white

BASE_CELL_PADDING = [
    ("GRID", (0, 0), (-1, -1), 0.5, SLATE_200),
    ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]


def safe_xml(value: str) -> str:
    """Escapa caracteres XML preservando tildes, ñ y saltos de línea básicos."""
    return escape(str(value or "")).replace("\n", "<br/>")


def build_acta_styles() -> dict[str, ParagraphStyle]:
    """Construye hoja de estilos institucionales para ReportLab Platypus."""
    return {
        "header_title": ParagraphStyle(
            "ActaHeaderTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "header_sub": ParagraphStyle(
            "ActaHeaderSub",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#D1FAE5"),
            alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "ActaSection",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=UTS_EMERALD,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ActaBody",
            fontName="Helvetica",
            fontSize=9,
            leading=12.5,
            textColor=SLATE_700,
            alignment=TA_LEFT,
        ),
        "body_bold": ParagraphStyle(
            "ActaBodyBold",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12.5,
            textColor=SLATE_900,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "ActaSmall",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=SLATE_500,
            alignment=TA_LEFT,
        ),
        "table_header": ParagraphStyle(
            "ActaTableHeader",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "table_cell": ParagraphStyle(
            "ActaTableCell",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=SLATE_700,
            alignment=TA_LEFT,
        ),
        "table_num": ParagraphStyle(
            "ActaTableNum",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=SLATE_900,
            alignment=TA_RIGHT,
        ),
        "sign_label": ParagraphStyle(
            "ActaSignLabel",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=SLATE_900,
            alignment=TA_CENTER,
        ),
    }


def draw_page_footer(canvas, doc) -> None:
    """Dibuja pie de página institucional con numeración en cada página."""
    canvas.saveState()
    width, _ = doc.pagesize
    canvas.setStrokeColor(SLATE_200)
    canvas.setLineWidth(0.75)
    canvas.line(doc.leftMargin, 36, width - doc.rightMargin, 36)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE_500)
    canvas.drawString(
        doc.leftMargin,
        24,
        "TutoIA · Unidades Tecnológicas de Santander (UTS) · Insumo técnico de apoyo al jurado",
    )
    canvas.drawRightString(width - doc.rightMargin, 24, f"Página {canvas.getPageNumber()}")
    canvas.restoreState()
