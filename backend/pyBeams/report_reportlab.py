# report_reportlab.py
# Generación del reporte técnico en PDF usando ReportLab (sin dependencias de
# LaTeX), para poder generarlo en cualquier servidor Python estándar.
#
# Uso desde código:
# from report_reportlab import generar_reporte_pdf_bytes

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, HRFlowable,
)
from reportlab.platypus.flowables import KeepTogether

MAIN_BLUE = colors.HexColor("#2E5B8A")
LIGHT_BLUE = colors.HexColor("#D6E4F0")
DARK_GRAY = colors.HexColor("#3D3D3D")
OK_GREEN = colors.HexColor("#1A7A3A")
ERR_RED = colors.HexColor("#B22222")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PBTitle", fontSize=26, leading=32, textColor=colors.white,
        alignment=TA_CENTER, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="PBSubtitle", fontSize=13, leading=18, textColor=LIGHT_BLUE,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="PBSection", fontSize=15, leading=20, textColor=MAIN_BLUE,
        spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="PBSubsection", fontSize=11.5, leading=16, textColor=DARK_GRAY,
        spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="PBBody", fontSize=10, leading=14.5, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="PBCaption", fontSize=8.5, leading=11, textColor=colors.gray,
        alignment=TA_CENTER, spaceBefore=2, spaceAfter=10,
    ))
    return styles


def _table(data, col_widths, header_bg=MAIN_BLUE):
    table = Table(data, colWidths=col_widths, hAlign="CENTER", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B0B0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index in range(1, len(data)):
        if row_index % 2 == 0:
            style.append(("BACKGROUND", (0, row_index), (-1, row_index), LIGHT_BLUE))
    table.setStyle(TableStyle(style))
    return table


def _equilibrium_check(r_sol, f, typesloads):
    sum_Fy = 0.0
    sum_M0 = 0.0
    rows = []

    for key, load in f.items():
        val = load["value"]
        a = load["a"]
        a1 = load.get("a1", a)
        ltyp = load["type"]

        if ltyp == typesloads[0]:
            Fy = val
            M0 = val * a
            desc = f"{key} (puntual)"
        elif ltyp == typesloads[1]:
            length = a1 - a
            Fy = val * length
            M0 = Fy * (a + length / 2)
            desc = f"{key} (dist. unif.)"
        elif ltyp == typesloads[2]:
            length = a1 - a
            Fy = val * length / 2
            M0 = Fy * (a + length * 2 / 3)
            desc = f"{key} (tri. crec.)"
        elif ltyp == typesloads[3]:
            length = abs(a - a1)
            Fy = val * length / 2
            M0 = Fy * (a + length / 3)
            desc = f"{key} (tri. dec.)"
        elif ltyp == typesloads[4]:
            Fy = 0.0
            M0 = val
            desc = f"{key} (momento)"
        else:
            continue

        sum_Fy += Fy
        sum_M0 += M0
        rows.append((desc, f"{Fy:.3f}", f"{M0:.3f}"))

    for name, data in r_sol.items():
        val = data["value"]
        pos = data["a"]
        tipo = data["type"]

        if tipo == typesloads[0]:
            Fy = val
            M0 = val * pos
            desc = f"R_{name} (reacción)"
        else:
            Fy = 0.0
            M0 = val
            desc = f"M_{name} (momento reac.)"

        sum_Fy += Fy
        sum_M0 += M0
        rows.append((desc, f"{Fy:.3f}", f"{M0:.3f}"))

    return sum_Fy, sum_M0, rows


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(MAIN_BLUE)
    canvas.setLineWidth(0.6)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.gray)
    canvas.drawString(2 * cm, A4[1] - 1.3 * cm, "PyBeams — Análisis Estructural de Vigas")
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.3 * cm, datetime.today().strftime("%d/%m/%Y"))
    canvas.line(2 * cm, A4[1] - 1.5 * cm, A4[0] - 2 * cm, A4[1] - 1.5 * cm)

    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.drawString(2 * cm, 1.1 * cm, "Elaborado por: Kenneth Prieto")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Pág. {doc.page}")
    canvas.restoreState()


def generar_reporte_pdf_bytes(l, Sy, FS, r_sol, r, f, Mmax, s_cm3, typesloads,
                               imagen_dcl_bytes=None, imagen_diagramas_bytes=None):
    """
    Genera el reporte técnico de la viga en PDF y retorna los bytes del archivo.

    Args:
        l, Sy, FS (float): geometría y propiedades del material.
        r_sol (dict): reacciones calculadas.
        r (dict): apoyos definidos.
        f (dict): cargas aplicadas.
        Mmax (float): momento flector máximo [kN.m].
        s_cm3 (float): módulo de sección requerido [cm3].
        typesloads (list): tipos de carga reconocidos por el sistema.
        imagen_dcl_bytes (bytes): PNG del diagrama de cuerpo libre.
        imagen_diagramas_bytes (bytes): PNG de los diagramas V/M.

    Returns:
        bytes: contenido del archivo PDF.
    """
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    sigmaAllow_MPa = Sy / FS
    n_dof = sum(row["dof"] for row in r.values())
    fecha_hoy = datetime.today().strftime("%d/%m/%Y")

    story = []

    # ── Portada ──────────────────────────────────────────────────────────
    portada = Table(
        [[Paragraph("Reporte de Cálculo<br/>Estructural de Viga", styles["PBTitle"])],
         [Paragraph("Análisis estático por el método de funciones de singularidad", styles["PBSubtitle"])]],
        colWidths=[doc.width],
    )
    portada.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), MAIN_BLUE),
        ("TOPPADDING", (0, 0), (-1, 0), 60),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 60),
    ]))
    story.append(Spacer(1, 4 * cm))
    story.append(portada)
    story.append(Spacer(1, 2 * cm))

    meta_rows = [
        ["Elaborado por:", "Kenneth Prieto"],
        ["Herramienta:", "PyBeams — Sistema de Análisis de Vigas"],
        ["Fecha:", fecha_hoy],
    ]
    meta_table = Table(meta_rows, colWidths=[4 * cm, doc.width - 4 * cm], hAlign="RIGHT")
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "Documento generado automáticamente a partir de los parámetros de entrada.",
        ParagraphStyle(name="PBFootnote", fontSize=9, textColor=colors.gray, alignment=TA_CENTER),
    ))
    story.append(PageBreak())

    # ── 1. Diagrama de cuerpo libre ─────────────────────────────────────
    story.append(Paragraph("1. Diagrama de Cuerpo Libre", styles["PBSection"]))
    story.append(Paragraph(
        "El siguiente diagrama representa las condiciones de sujeción y las cargas "
        "externas aplicadas sobre la viga, tal como fueron definidas como datos de "
        "entrada del análisis.",
        styles["PBBody"],
    ))
    if imagen_dcl_bytes:
        img = Image(io.BytesIO(imagen_dcl_bytes), width=doc.width, height=doc.width * 0.42)
        story.append(img)
        story.append(Paragraph("Figura 1. Diagrama de cuerpo libre de la viga.", styles["PBCaption"]))

    # ── 2. Parámetros iniciales ─────────────────────────────────────────
    story.append(Paragraph("2. Parámetros Iniciales y Propiedades del Material", styles["PBSection"]))
    param_rows = [
        ["Variable / Parámetro", "Valor", "Unidades"],
        ["Longitud de la viga (l)", f"{l:.2f}", "m"],
        ["Esfuerzo de fluencia (Sy)", f"{Sy:.2f}", "MPa"],
        ["Factor de Seguridad (FS)", f"{FS:.2f}", "---"],
        ["Esfuerzo admisible (σ adm)", f"{sigmaAllow_MPa:.2f}", "MPa"],
        ["Grado de hiperestaticidad (n)", str(n_dof), "---"],
    ]
    story.append(_table(param_rows, [doc.width * 0.5, doc.width * 0.25, doc.width * 0.25]))

    # ── 3. Configuración de apoyos ──────────────────────────────────────
    story.append(Paragraph("3. Configuración de Apoyos", styles["PBSection"]))
    dof_desc = {1: "1 reacción (Fy)", 2: "2 reacciones (Fy, M)"}
    apoyo_rows = [["ID", "Ubicación [m]", "Tipo", "Restricciones"]]
    for key, sup in r.items():
        apoyo_rows.append([
            key, f"{sup.get('location', 0):.2f}", sup.get("type", "-"),
            dof_desc.get(sup.get("dof", 1), str(sup.get("dof", 1))),
        ])
    story.append(_table(apoyo_rows, [doc.width * 0.15, doc.width * 0.25, doc.width * 0.3, doc.width * 0.3]))

    # ── 4. Cargas externas aplicadas ────────────────────────────────────
    story.append(Paragraph("4. Cargas Externas Aplicadas", styles["PBSection"]))
    unit_map = {
        typesloads[0]: "kN", typesloads[1]: "kN/m", typesloads[2]: "kN/m",
        typesloads[3]: "kN/m", typesloads[4]: "kN.m",
    }
    carga_rows = [["ID", "Tipo de carga", "Magnitud", "a [m]", "a1 [m]", "Unidad"]]
    for key, load in f.items():
        pos_a1 = load.get("a1", "---")
        a1_str = f"{pos_a1:.2f}" if isinstance(pos_a1, (int, float)) else str(pos_a1)
        carga_rows.append([
            key, load.get("type", "---"), f"{load.get('value', 0.0):.2f}",
            f"{load.get('a', 0.0):.2f}", a1_str, unit_map.get(load.get("type"), "---"),
        ])
    story.append(_table(carga_rows, [doc.width * x for x in (0.08, 0.32, 0.16, 0.14, 0.14, 0.16)]))

    # ── 5. Reacciones en los apoyos ─────────────────────────────────────
    story.append(Paragraph("5. Reacciones en los Apoyos", styles["PBSection"]))
    reac_rows = [["Reacción", "Posición [m]", "Valor", "Unidad", "Sentido"]]
    for name, data in r_sol.items():
        val = data.get("value", 0.0)
        unid = "kN" if data.get("type") == typesloads[0] else "kN.m"
        reac_rows.append([
            name, f"{data.get('a', 0.0):.2f}", f"{val:.4f}", unid,
            "positivo" if val >= 0 else "negativo",
        ])
    story.append(_table(reac_rows, [doc.width * x for x in (0.2, 0.2, 0.2, 0.2, 0.2)]))

    # ── 6. Verificación de equilibrio ───────────────────────────────────
    story.append(Paragraph("6. Verificación de Equilibrio", styles["PBSection"]))
    story.append(Paragraph(
        "Como control de calidad del resultado, se verifica que la sumatoria de "
        "fuerzas verticales y la sumatoria de momentos respecto al origen sean "
        "nulas, confirmando el equilibrio estático del sistema.",
        styles["PBBody"],
    ))
    sum_Fy, sum_M0, eq_rows = _equilibrium_check(r_sol, f, typesloads)
    eq_table_rows = [["Elemento", "Fy [kN]", "M_O [kN.m]"]] + [list(row) for row in eq_rows]
    story.append(_table(eq_table_rows, [doc.width * 0.5, doc.width * 0.25, doc.width * 0.25]))
    story.append(Spacer(1, 0.3 * cm))

    tol = 1e-4
    ok_Fy = abs(sum_Fy) < tol
    ok_M = abs(sum_M0) < tol
    estado_style = ParagraphStyle(name="PBEstado", fontSize=10.5, alignment=TA_CENTER, fontName="Helvetica-Bold")
    story.append(Paragraph(
        f'ΣFy = {sum_Fy:.2e} kN &nbsp;&rArr;&nbsp; '
        f'<font color="{"#1A7A3A" if ok_Fy else "#B22222"}">'
        f'{"EQUILIBRADO" if ok_Fy else "ERROR"}</font>',
        estado_style,
    ))
    story.append(Paragraph(
        f'ΣM_O = {sum_M0:.2e} kN·m &nbsp;&rArr;&nbsp; '
        f'<font color="{"#1A7A3A" if ok_M else "#B22222"}">'
        f'{"EQUILIBRADO" if ok_M else "ERROR"}</font>',
        estado_style,
    ))

    # ── 7. Diagramas de cortante y momento flector ──────────────────────
    story.append(PageBreak())
    story.append(Paragraph("7. Diagramas de Fuerza Cortante y Momento Flector", styles["PBSection"]))
    story.append(Paragraph(
        "Los diagramas V(x) y M(x) se obtienen mediante la integración numérica "
        "de las funciones de singularidad a lo largo del eje de la viga.",
        styles["PBBody"],
    ))
    if imagen_diagramas_bytes:
        img = Image(io.BytesIO(imagen_diagramas_bytes), width=doc.width * 0.85, height=doc.width * 0.85 * 0.8)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Paragraph("Figura 2. Diagramas V(x) y M(x) a lo largo de la viga.", styles["PBCaption"]))
    story.append(Paragraph(
        f"El <b>momento flector máximo absoluto</b> registrado es <b>|M|max = {Mmax:.2f} kN·m</b>.",
        styles["PBBody"],
    ))

    # ── 8. Diseño de la sección transversal ─────────────────────────────
    story.append(Paragraph("8. Diseño de la Sección Transversal", styles["PBSection"]))
    story.append(Paragraph(
        "A partir del momento flector máximo y del esfuerzo admisible se determina "
        "el módulo de sección mínimo requerido.",
        styles["PBBody"],
    ))
    story.append(Paragraph("Esfuerzo admisible", styles["PBSubsection"]))
    story.append(Paragraph(
        f"σ_adm = Sy / FS = {Sy:.0f} MPa / {FS:.2f} = <b>{sigmaAllow_MPa:.2f} MPa</b>",
        styles["PBBody"],
    ))
    story.append(Paragraph("Módulo de sección requerido", styles["PBSubsection"]))
    story.append(Paragraph(
        f"s = Mmax / σ_adm = {Mmax:.2f} kN·m / ({sigmaAllow_MPa:.2f} × 10³ kN/m²) "
        f"= <b>{s_cm3:.2f} cm³</b>",
        styles["PBBody"],
    ))
    story.append(Paragraph(
        "Con el valor de s calculado se debe consultar el catálogo de perfiles "
        "laminados (p. ej. perfiles W, IPE, HEA) y seleccionar el perfil cuyo "
        "módulo de sección Sx sea igual o inmediatamente superior al valor requerido.",
        styles["PBBody"],
    ))

    # ── 9. Resumen ejecutivo ────────────────────────────────────────────
    story.append(Paragraph("9. Resumen Ejecutivo", styles["PBSection"]))
    resumen_rows = [
        ["Longitud de la viga", f"l = {l:.2f} m"],
        ["Material / Norma", f"Sy = {Sy:.0f} MPa"],
        ["Factor de seguridad", f"FS = {FS:.1f}"],
        ["Esfuerzo admisible", f"σ_adm = {sigmaAllow_MPa:.2f} MPa"],
        ["Momento flector máximo", f"|M|max = {Mmax:.2f} kN·m"],
        ["Módulo de sección requerido", f"s_req = {s_cm3:.2f} cm³"],
        ["Grado de hiperestaticidad", f"n = {n_dof} ecuaciones"],
    ]
    resumen_table = Table(resumen_rows, colWidths=[doc.width * 0.5, doc.width * 0.5])
    resumen_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, MAIN_BLUE),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.white),
    ]))
    story.append(KeepTogether([resumen_table]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
