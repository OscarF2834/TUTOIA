"""
Tutoia · Generador del acta de evaluación.

Produce un documento HTML autocontenido —con gráficas SVG nativas— que:
· Consigna los datos institucionales de la sesión (acta sumativa).
· Presenta la nota consolidada con su banda cualitativa.
· Desglosa la nota por criterio de la rúbrica (barras + radar).
· Traza la línea de tiempo del desempeño pregunta por pregunta.
· Se recibe en un navegador, se imprime a PDF (Ctrl+P) o se archiva.

La salida es un solo archivo: sin dependencias de render ni imágenes
externas, listo para evidenciar el proyecto en la fase de validación.
"""
import html
import math
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.services.evaluator import BANDAS, CRITERIOS, banda_de


# ═══════════════════════════════════════════════════════════════════
#  Construcción del acta
# ═══════════════════════════════════════════════════════════════════
def generar_acta(sesion) -> Path:
    """Genera y persiste el acta de la sesión. Devuelve la ruta del archivo."""
    escape = lambda s: html.escape(str(s), quote=False)  # noqa: E731

    # ── Cifras consolidadas ────────────────────────────────────────
    nota = sesion.nota_final if sesion.nota_final is not None else 0.0
    banda_etiqueta, banda_desc = banda_de(nota)
    fecha = datetime.fromtimestamp(sesion.creada).strftime("%d de %B de %Y · %H:%M")
    # Cromamos la fecha en español si el entorno lo permite (fallback manual)
    MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_fmt = (
        f"{datetime.fromtimestamp(sesion.creada).day} de "
        f"{MESES[datetime.fromtimestamp(sesion.creada).month - 1]} de "
        f"{datetime.fromtimestamp(sesion.creada).year} · "
        f"{datetime.fromtimestamp(sesion.creada):%H:%M}"
    )

    # Promedio por criterio (lo que ve el radar)
    por_criterio: dict[str, float] = {}
    for crit in CRITERIOS:
        cod = crit["codigo"]
        valores = [
            t.criterios[cod]["puntaje"]
            for t in sesion.turnos
            if cod in t.criterios
        ]
        por_criterio[cod] = round(sum(valores) / len(valores), 2) if valores else 0.0

    esc = lambda v: escape(v)  # noqa: E731

    # ── Bloques HTML ───────────────────────────────────────────────
    filas_criterios = "".join(
        _fila_criterio(crit, por_criterio[crit["codigo"]])
        for crit in CRITERIOS
    )

    filas_turnos = "".join(_fila_turno(i, t) for i, t in enumerate(sesion.turnos, 1))
    radar = _svg_radar(por_criterio)
    timeline = _svg_historial(sesion.turnos)

    html_acta = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Acta de evaluación · Tutoia · {esc(sesion.estudiante)}</title>
<style>
  :root {{
    --panel: #ffffff; --accent: #047857; --gold: #b45309;
    --texto: #12251c; --suave: #51665c; --linea: #d9e7df;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 40px 32px; font-family: 'Segoe UI', Roboto, Arial, sans-serif;
    background: #f4f9f6; color: #12251c; line-height: 1.55;
  }}
  .documento {{ max-width: 900px; margin: 0 auto; }}
  .encabezado {{
    display: flex; gap: 20px; align-items: center;
    border-bottom: 2px solid #d9e7df; padding-bottom: 18px; margin-bottom: 26px;
  }}
  .logo {{
    width: 62px; height: 62px; border-radius: 14px; flex: none;
    background: linear-gradient(135deg, #10b981, #0d9488);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 700; color: white;
  }}
  .titulo h1 {{ margin: 0; font-size: 22px; letter-spacing: 0.5px; color: #12251c; }}
  .titulo p {{ margin: 2px 0 0; color: #51665c; font-size: 13px; }}
  .sello {{
    margin-left: auto; text-align: right; color: #51665c; font-size: 12px;
  }}
  .sello b {{ color: #047857; letter-spacing: 1px; }}
  .datos {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
    background: #ffffff; border: 1px solid #d9e7df; border-radius: 14px;
    padding: 18px; margin-bottom: 24px; font-size: 14px;
  }}
  .datos b {{ color: #51665c; font-weight: 700; display: block; font-size: 11px;
              text-transform: uppercase; letter-spacing: 0.8px; }}
  .resumen_tesis {{
    font-style: italic; color: #51665c; font-size: 12.5px; margin-top: 6px;
  }}
  .nota-caja {{
    display: flex; gap: 22px; align-items: center;
    background: linear-gradient(135deg, #ffffff, #eaf7f1);
    border: 1px solid #b9d5c8; border-radius: 16px; padding: 22px; margin-bottom: 26px;
  }}
  .nota-num {{ font-size: 52px; font-weight: 800; color: #b45309; line-height: 1; }}
  .nota-num small {{ font-size: 20px; color: #7d9188; font-weight: 500; }}
  .banda h2 {{ margin: 0 0 4px; font-size: 19px; color: #12251c; }}
  .banda p {{ margin: 0; color: #51665c; font-size: 13px; }}
  section {{ margin-bottom: 28px; }}
  h3 {{
    font-size: 14px; text-transform: uppercase; letter-spacing: 1.2px;
    color: #047857; margin: 0 0 14px;
    border-bottom: 1px solid #d9e7df; padding-bottom: 8px;
  }}
  .grid-doble {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; align-items: start; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #d9e7df; vertical-align: top; }}
  th {{ color: #51665c; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; }}
  .chip {{
    display: inline-block; min-width: 40px; text-align: center; padding: 3px 8px;
    border-radius: 20px; font-weight: 700; font-size: 12px;
    background: #eaf7f1; color: #047857;
  }}
  .chip.alto {{ background: #e7f6ed; color: #065f46; }}
  .chip.medio {{ background: #fff7ec; color: #b45309; }}
  .chip.bajo {{ background: #fdeeec; color: #b91c1c; }}
  .eje-chip {{ color: #51665c; font-size: 11px; }}
  .respuesta-previa {{ color: #51665c; font-size: 12px; margin: 4px 0 0; }}
  .pie {{
    margin-top: 36px; padding-top: 14px; border-top: 1px solid #d9e7df;
    color: #7d9188; font-size: 11px; display: flex; justify-content: space-between;
  }}
  .acciones {{ position: fixed; top: 16px; right: 16px; }}
  .btn-print {{
    background: #047857; color: white; border: none; padding: 10px 16px;
    border-radius: 10px; font-size: 13px; cursor: pointer; font-weight: 600;
  }}
  @media print {{
    body {{ background: white; color: #1a2233; padding: 0; }}
    .documento {{ max-width: none; }}
    .acciones {{ display: none; }}
    .nota-caja {{ border-color: #c9d4e8; background: #f2f6fc; }}
    .encabezado, section h3 {{ border-color: #c9d4e8; }}
  }}
</style>
</head>
<body>
<div class="acciones"><button class="btn-print" onclick="window.print()">⎙  Imprimir / Guardar PDF</button></div>
<div class="documento">

  <div class="encabezado">
    <div class="logo">T</div>
    <div class="titulo">
      <h1>Acta de evaluación · Sustentación de trabajo de grado</h1>
      <p>Generada automáticamente por <b>AURA</b> — Avatar evaluador · Tutoia v{settings.VERSION}</p>
    </div>
    <div class="sello">
      <b>TUTOIA</b><br>Unidades Tecnológicas<br>de Santander<br>Periodo 2026
    </div>
  </div>

  <div class="datos">
    <div><b>Sustentante</b>{esc(sesion.estudiante)}</div>
    <div><b>Fecha de la sesión</b>{fecha_fmt}</div>
    <div><b>Tema del trabajo de grado</b>{esc(sesion.tema)}</div>
    <div><b>Motor analítico activo</b>{esc(sesion.motor_usado or "heurístico-local")}</div>
    <div style="grid-column: 1 / -1"><b>Resumen evaluado</b>
      <div class="resumen_tesis">“{esc(sesion.resumen or "No se registró resumen de la tesis.")}”</div>
    </div>
  </div>

  <div class="nota-caja">
    <div class="nota-num">{nota:.1f}<small> / 5.0</small></div>
    <div class="banda">
      <h2>Banda: {esc(banda_etiqueta)}</h2>
      <p>{escape(banda_desc)}</p>
    </div>
  </div>

  <section>
    <h3>Desempeño por criterio de la rúbrica institucional</h3>
    <div class="grid-doble">
      <table>
        <tr><th>Criterio</th><th>Peso</th><th>Media</th><th>Nivel</th></tr>
        {filas_criterios}
      </table>
      <div style="text-align:center">{radar}</div>
    </div>
  </section>

  <section>
    <h3>Línea de tiempo de la sustentación</h3>
    {timeline}
  </section>

  <section>
    <h3>Detallaje pregunta por pregunta</h3>
    <table>
      <tr><th>#</th><th>Eje temático</th><th>Nota</th><th>Fortalezas y oportunidades registradas</th></tr>
      {filas_turnos}
    </table>
  </section>

  <section>
    <h3>Escala cualitativa institucional</h3>
    <table>
      {"".join(f"<tr><td class='chip {_clase_chip(u)}'>{e}</td><td>{escape(d)}</td></tr>" for u, e, d in BANDAS)}
    </table>
  </section>

  <div class="pie">
    <span>Documento emitido por la plataforma <b>TUTOIA</b> · v{settings.VERSION} · 2026</span>
    <span>Este acta es un insumo de apoyo; el concepto final corresponde al jurado humano.</span>
  </div>

</div>
</body>
</html>"""

    ruta = settings.REPORTES_DIR / f"acta_{sesion.id}.html"
    ruta.write_text(html_acta, encoding="utf-8")
    return ruta


# ═══════════════════════════════════════════════════════════════════
#  Bloques SVG y helpers de la plantilla
# ═══════════════════════════════════════════════════════════════════
def _clase_chip(nota: float) -> str:
    if nota >= 4.0:
        return "alto"
    if nota >= 2.5:
        return "medio"
    return "bajo"


def _fila_criterio(crit: dict, media: float) -> str:
    etiqueta = html.escape(crit["etiqueta"])
    return (
        f"<tr><td><b>{etiqueta}</b><br><span style='color:#9aa8c7;font-size:11px;'>"
        f"{html.escape(crit['descriptor'][:96])}…</span></td>"
        f"<td>{crit['peso']:.0%}</td>"
        f"<td><span class='chip {_clase_chip(media)}'>{media:.1f}</span></td>"
        f"<td style='color:#9aa8c7'>{_nivel_de(media)}</td></tr>"
    )


def _nivel_de(nota: float) -> str:
    if nota >= 4.5: return "Dominio sobresaliente"
    if nota >= 3.5: return "Dominio sólido"
    if nota >= 2.5: return "Comprensión parcial con vacíos"
    if nota >= 1.5: return "Débil"
    return "Inadecuado"


def _fila_turno(indice: int, turno) -> str:
    frz = turno.fortalezas or ["(sin fortalezas destacadas)"]
    oport = turno.oportunidades or ["(sin observaciones)"]
    contenido = "".join(
        f"<li style='color:#6ee7a0'>✓ {html.escape(x)}</li>" for x in frz[:2]
    ) + "".join(
        f"<li style='color:#ffd57e'>▲ {html.escape(x)}</li>" for x in oport[:2]
    )
    tipo = "" if turno.tipo == "principal" else " <span class='eje-chip'>(refuerzo)</span>"
    return (
        f"<tr><td>{indice}</td>"
        f"<td><b>{html.escape(turno.eje_etiqueta)}</b>{tipo}<br>"
        f"<span class='eje-chip'>{html.escape(turno.pregunta[:110])}</span></td>"
        f"<td><span class='chip {_clase_chip(turno.nota_global or 0)}'>{turno.nota_global or 0:.1f}</span></td>"
        f"<td><ul style='margin:0;padding-left:16px;font-size:12px'>{contenido}</ul></td></tr>"
    )


def _svg_radar(por_criterio: dict[str, float]) -> str:
    """
    Radar de criterios en SVG puro: 4 ejes, polígono escalado 0–5.
    """
    codigos = [c["codigo"] for c in CRITERIOS]
    n = len(codigos)
    cx, cy, radio = 130.0, 128.0, 100.0

    def punto(i: int, razon: float) -> tuple[float, float]:
        ang = -math.pi / 2 + i * (2 * math.pi / n)
        return (
            round(cx + radio * razon * math.cos(ang), 1),
            round(cy + radio * razon * math.sin(ang), 1),
        )

    html_str = ["<svg width='260' height='256' viewBox='0 0 260 256'>"]
    # Anillos de referencia (0, 2.5, 5)
    for razon, _color in ((0.25, "#26314f"), (0.5, "#26314f"), (0.75, "#26314f"), (1.0, "#3a4a72")):
        pts = " ".join(f"{x},{y}" for x, y in (punto(i, razon) for i in range(n)))
        opacidad = "1" if razon == 1.0 else "0.55"
        html_str.append(
            f"<polygon points='{pts}' fill='none' stroke='#26314f' stroke-opacity='{opacidad}'/>"
        )
    # Ejes y etiquetas
    for i, cod in enumerate(codigos):
        x, y = punto(i, 1.0)
        html_str.append(f"<line x1='{cx}' y1='{cy}' x2='{x}' y2='{y}' stroke='#26314f'/>")
        lx, ly = punto(i, 1.18)
        etiqueta = html.escape(
            {"pertinencia": "Pertinencia", "coherencia": "Coherencia",
             "fundamentacion": "Fundamentación", "metodologia": "Método"}[cod]
        )
        ancla = "middle" if abs(lx - cx) < 10 else ("start" if lx > cx else "end")
        html_str.append(
            f"<text x='{lx}' y='{ly}' fill='#9aa8c7' font-size='10' text-anchor='{ancla}'"
            f" dominant-baseline='middle'>{etiqueta}</text>"
        )
    # Polígono de datos
    pts = " ".join(f"{x},{y}" for x, y in (
        punto(i, min(1.0, por_criterio.get(c, 0.0) / 5.0)) for i, c in enumerate(codigos)
    ))
    html_str.append(
        f"<polygon points='{pts}' fill='#10b981' fill-opacity='0.3' stroke='#047857' stroke-width='2'/>"
    )
    for i, cod in enumerate(codigos):
        x, y = punto(i, min(1.0, por_criterio.get(cod, 0.0) / 5.0))
        html_str.append(f"<circle cx='{x}' cy='{y}' r='3.5' fill='#b45309'/>")

    html_str.append(
        f"<text x='{cx}' y='{252}' fill='#6c7ba3' font-size='9' text-anchor='middle'>"
        "Media por criterio · escala 0–5</text></svg>"
    )
    return "".join(html_str)


def _svg_historial(turnos: list) -> str:
    """Gráfica de barras: nota por turno (principal vs refuerzo)."""
    if not turnos:
        return "<p style='color:#6c7ba3'>Sin turnos registrados.</p>"

    ancho_barra, hueco, altura = 26, 10, 110
    total = len(turnos)
    ancho_svg = total * (ancho_barra + hueco) + 20
    barras = []
    for i, t in enumerate(turnos):
        nota = (t.nota_global or 0.0) / 5.0
        h = max(2.0, nota * altura)
        x = 16 + i * (ancho_barra + hueco)
        y = altura + 8 - h
        es_seguimiento = t.tipo != "principal"
        color = "#0d9488" if es_seguimiento else "#047857"
        barras.append(
            f"<rect x='{x}' y='{y:.1f}' width='{ancho_barra}' height='{h:.1f}' rx='4' fill='{color}'>"
            f"<title>Pregunta {i + 1} · {t.eje_etiqueta}: {t.nota_global or 0:.1f}/5.0</title></rect>"
            f"<text x='{x + ancho_barra / 2}' y='{altura + 24}' fill='#6c7ba3' font-size='9' "
            f"text-anchor='middle'>{i + 1}</text>"
            f"<text x='{x + ancho_barra / 2}' y='{y - 5:.1f}' fill='#e9b44c' font-size='9' "
            f"font-weight='700' text-anchor='middle'>{t.nota_global or 0:.1f}</text>"
        )
    leyenda = (
        "<g transform='translate(16,4)'>"
        "<rect width='10' height='10' rx='2' fill='#1c72e4'/>"
        "<text x='14' y='9' fill='#9aa8c7' font-size='9'>Pregunta principal</text>"
        "<rect x='130' width='10' height='10' rx='2' fill='#7c3aed'/>"
        "<text x='144' y='9' fill='#9aa8c7' font-size='9'>Refuerzo adaptativo</text></g>"
    )
    return (
        f"<svg width='{ancho_svg}' height='150' style='max-width:100%'>"
        f"{leyenda}<line x1='10' y1='{altura + 8}' x2='{ancho_svg - 8}' y2='{altura + 8}' "
        f"stroke='#26314f'/>{''.join(barras)}</svg>"
    )
