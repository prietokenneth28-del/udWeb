# report.py
# Generación automatizada de reportes técnicos en formato PDF utilizando PyLaTeX.
#
# Uso desde linea de comandos:
# N/A. Se importa como módulo: from report import generar_reporte_pdf
#
# Flujo:
# 1. Inicializa el documento LaTeX con configuración y paquetes específicos.
# 2. Inserta la información del proyecto, propiedades del material y geometría.
# 3. Construye tablas dinámicas con los valores de las cargas y las reacciones calculadas.
# 4. Embebe las imágenes de los diagramas estructurales previamente generados.
# 5. Compila el documento (.tex) y genera el archivo .pdf de salida.

import os
import numpy as np
import pandas as pd
from datetime import datetime

from pylatex import (
    Document, Section, Subsection, Table, Command, Figure,
    MultiColumn, Package, Alignat, NewPage, HorizontalSpace,
    VerticalSpace, LineBreak, NewLine, PageStyle, Head, Foot,
    HFill, MiniPage, TextColor, Center
)
from pylatex.utils import NoEscape, bold, italic


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _booktabs_table(doc, caption, col_fmt, header_cells, rows):
    """
    Renders a booktabs-style table with a coloured header row and
    alternating row shading. No vertical rules.
    """
    with doc.create(Table(position='H')) as table:
        table.add_caption(caption)
        table.append(NoEscape(r'\centering'))
        table.append(NoEscape(r'\small'))
        table.append(NoEscape(rf'\begin{{tabular}}{{{col_fmt}}}'))
        table.append(NoEscape(r'\toprule'))

        header_tex = " & ".join(
            [rf'\textbf{{\textcolor{{white}}{{{h}}}}}' for h in header_cells]
        )
        table.append(NoEscape(
            rf'\rowcolor{{mainblue}} {header_tex} \\'
        ))
        table.append(NoEscape(r'\midrule'))

        for i, row in enumerate(rows):
            row_tex = " & ".join(row)
            if i % 2 == 1:
                table.append(NoEscape(rf'\rowcolor{{lightblue}} {row_tex} \\'))
            else:
                table.append(NoEscape(rf'{row_tex} \\'))

        table.append(NoEscape(r'\bottomrule'))
        table.append(NoEscape(r'\end{tabular}'))


def _summary_box(doc, items):
    """
    Inserts a tcolorbox summary card with key-value pairs.
    """
    lines = r"\\ ".join(
        [rf"\textbf{{{lbl}:}} \hfill {val}" for lbl, val in items]
    )
    doc.append(NoEscape(
        r"\begin{tcolorbox}["
        r"colback=lightblue, colframe=mainblue, "
        r"arc=4pt, boxrule=0.8pt, "
        r"title={\textbf{Resumen Ejecutivo}}, "
        r"coltitle=white, fonttitle=\bfseries, "
        r"attach boxed title to top left={yshift=-2mm, xshift=4mm}]"
        rf"\small {lines}"
        r"\end{tcolorbox}"
    ))


def _equilibrium_check(r_sol, f, typesloads):
    """
    Computes ΣFy and ΣM₀ contributions from loads and reactions.
    Returns (sum_Fy, sum_M0, rows) where rows is a list of
    [desc, Fy_str, M0_str] for the table.
    """
    sum_Fy = 0.0
    sum_M0 = 0.0
    rows = []

    for key, load in f.items():
        val  = load['value']
        a    = load['a']
        a1   = load.get('a1', a)
        ltyp = load['type']

        if ltyp == typesloads[0]:
            Fy = val;  M0 = val * a
            desc = rf"{key} (puntual)"
        elif ltyp == typesloads[1]:
            length = a1 - a
            Fy = val * length;  M0 = Fy * (a + length / 2)
            desc = rf"{key} (dist. unif.)"
        elif ltyp == typesloads[2]:
            length = a1 - a
            Fy = val * length / 2;  M0 = Fy * (a + length * 2 / 3)
            desc = rf"{key} (tri. crec.)"
        elif ltyp == typesloads[3]:
            length = abs(a - a1)
            Fy = val * length / 2;  M0 = Fy * (a + length / 3)
            desc = rf"{key} (tri. dec.)"
        elif ltyp == typesloads[4]:
            Fy = 0.0;  M0 = val
            desc = rf"{key} (momento)"
        else:
            continue

        sum_Fy += Fy;  sum_M0 += M0
        rows.append((desc, f"{Fy:.3f}", f"{M0:.3f}"))

    for name, data in r_sol.items():
        val  = data['value']
        pos  = data['a']
        tipo = data['type']

        if tipo == typesloads[0]:
            Fy = val;  M0 = val * pos
            desc = rf"R\textsubscript{{{name}}} (reaccion)"
        else:
            Fy = 0.0;  M0 = val
            desc = rf"M\textsubscript{{{name}}} (momento reac.)"

        sum_Fy += Fy;  sum_M0 += M0
        rows.append((desc, f"{Fy:.3f}", f"{M0:.3f}"))

    return sum_Fy, sum_M0, rows


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def generar_reporte_pdf(filename_prefix, l, Sy, FS, r_sol, r, f, Mmax,
                        typesloads, imagen_diagramas=None,
                        imagen_dcl=None, output_dir="."):
    """
    Genera un reporte tecnico profesional en PDF usando PyLaTeX.

    Args:
        filename_prefix (str) : Nombre base del archivo de salida (sin extension).
        l        (float)      : Longitud de la viga [m].
        Sy       (float)      : Esfuerzo de fluencia [MPa].
        FS       (float)      : Factor de seguridad.
        r_sol    (dict)       : Reacciones calculadas en los apoyos.
        r        (dict)       : Configuracion de apoyos.
        f        (dict)       : Cargas aplicadas.
        Mmax     (float)      : Momento flector maximo [kN.m].
        typesloads (list)     : Lista de tipos de carga del sistema.
        imagen_diagramas (str): Ruta PNG de los diagramas V-M.
        imagen_dcl       (str): Ruta PNG del diagrama de cuerpo libre.
        output_dir       (str): Directorio de salida.
    """

    # ── Directorio de salida ─────────────────────────────────────────────────
    if output_dir != ".":
        os.makedirs(output_dir, exist_ok=True)
    ruta_completa = os.path.join(output_dir, filename_prefix)

    # ── Valores derivados ────────────────────────────────────────────────────
    sigmaAllow_kPa = Sy * 1000 / FS
    sigmaAllow_MPa = Sy / FS
    s_m3           = Mmax / sigmaAllow_kPa
    s_cm3          = s_m3 * 100**3
    n_dof          = sum(row['dof'] for row in r.values())
    fecha_hoy      = datetime.today().strftime("%d/%m/%Y")

    # ── Documento ────────────────────────────────────────────────────────────
    geometry = {
        "left":   "2.5cm", "right":  "2.5cm",
        "top":    "3.0cm", "bottom": "2.5cm",
        "headheight": "14pt",
    }
    doc = Document(ruta_completa, geometry_options=geometry,
                   document_options=["12pt", "a4paper"])

    # ── Paquetes ─────────────────────────────────────────────────────────────
    pkgs = [
        ('inputenc',   ['utf8']),
        ('fontenc',    ['T1']),
        ('lmodern',    []),
        ('amsmath',    []),
        ('amssymb',    []),
        ('graphicx',   []),
        ('float',      []),
        ('booktabs',   []),
        ('xcolor',     ['table', 'dvipsnames']),
        ('colortbl',   []),
        ('caption',    []),
        ('subcaption', []),
        ('fancyhdr',   []),
        ('tcolorbox',  ['skins']),
        ('hyperref',   []),
        ('titlesec',   []),
        ('microtype',  []),
        ('parskip',    []),
        ('array',      []),
        ('multirow',   []),
        ('babel',      ['spanish']),
    ]
    for pkg, opts in pkgs:
        if opts:
            doc.packages.append(Package(pkg, options=opts))
        else:
            doc.packages.append(Package(pkg))

    # ── Preamble ─────────────────────────────────────────────────────────────
    doc.preamble.append(NoEscape(r"""
%% ── Colores corporativos ────────────────────────────────────────────────────
\definecolor{mainblue}{HTML}{2E5B8A}
\definecolor{lightblue}{HTML}{D6E4F0}
\definecolor{darkgray}{HTML}{3D3D3D}
\definecolor{midgray}{HTML}{7F7F7F}
\definecolor{okgreen}{HTML}{1A7A3A}
\definecolor{errred}{HTML}{B22222}

%% ── Hiperref (colores) ──────────────────────────────────────────────────────
\hypersetup{colorlinks=true, linkcolor=mainblue, urlcolor=mainblue}

%% ── Estilo de secciones ─────────────────────────────────────────────────────
\titleformat{\section}
  {\large\bfseries\color{mainblue}}
  {\thesection.}{0.6em}{}
  [\vspace{-4pt}\color{mainblue}\rule{\textwidth}{0.5pt}]

\titleformat{\subsection}
  {\normalsize\bfseries\color{darkgray}}
  {\thesubsection.}{0.5em}{}

%% ── Encabezado y pie de pagina ──────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textcolor{midgray}{PyBeams --- Analisis Estructural de Vigas}}
\fancyhead[R]{\small\textcolor{midgray}{\today}}
\fancyfoot[L]{\small\textcolor{midgray}{Elaborado por: Kenneth Prieto}}
\fancyfoot[R]{\small\textcolor{midgray}{Pag.\ \thepage}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}
\renewcommand{\headrule}{{\color{mainblue}\hrule width\headwidth height 0.4pt}}
\renewcommand{\footrule}{{\color{mainblue}\hrule width\headwidth height 0.4pt}}

%% ── Caption style ───────────────────────────────────────────────────────────
\captionsetup{font=small, labelfont={bf,color=mainblue}, textfont=it}
\captionsetup[table]{name=Tabla, skip=4pt}
\captionsetup[figure]{name=Figura}

%% ── tcolorbox library ───────────────────────────────────────────────────────
\tcbuselibrary{skins}
"""))

    # ══════════════════════════════════════════════════════════════════════════
    # PORTADA
    # ══════════════════════════════════════════════════════════════════════════
    doc.append(NoEscape(
        r"\begin{titlepage}" "\n"
        r"  \thispagestyle{empty}" "\n"
        r"  \pagecolor{mainblue}" "\n"
        r"  \vspace*{3cm}" "\n"
        r"  \begin{center}" "\n"
        r"    {\Huge\bfseries\textcolor{white}{Reporte de Calculo}}\\[0.4cm]" "\n"
        r"    {\Huge\bfseries\textcolor{white}{Estructural de Viga}}\\[1.2cm]" "\n"
        r"    \textcolor{white}{\rule{0.6\textwidth}{0.8pt}}\\[1.2cm]" "\n"
        r"    {\large\textcolor{lightblue}{Analisis estatico por el metodo de}}\\[0.2cm]" "\n"
        r"    {\large\textcolor{lightblue}{funciones de singularidad}}\\[2.5cm]" "\n"
        r"  \end{center}" "\n"
        r"  \begin{flushright}" "\n"
        r"    \textcolor{white}{\textbf{Elaborado por:}}\\[0.2cm]" "\n"
        r"    \textcolor{lightblue}{Kenneth Prieto}\\[0.6cm]" "\n"
        r"    \textcolor{white}{\textbf{Herramienta:}}\\[0.2cm]" "\n"
        r"    \textcolor{lightblue}{PyBeams --- Sistema de Analisis de Vigas}\\[0.6cm]" "\n"
        r"    \textcolor{white}{\textbf{Fecha:}}\\[0.2cm]" "\n"
        + rf"    \textcolor{{lightblue}}{{{fecha_hoy}}}" + "\n"
        r"  \end{flushright}" "\n"
        r"  \vfill" "\n"
        r"  \begin{center}" "\n"
        r"    \textcolor{lightblue}{\small\textit{"
        r"Documento generado automaticamente a partir de los parametros de entrada.}}" "\n"
        r"  \end{center}" "\n"
        r"\end{titlepage}" "\n"
        r"\nopagecolor" "\n"
    ))

    # ── Tabla de contenidos ──────────────────────────────────────────────────
    doc.append(NoEscape(
        r"\newpage" "\n"
        r"\tableofcontents" "\n"
        r"\newpage" "\n"
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # § 1  DIAGRAMA DE CUERPO LIBRE
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Diagrama de Cuerpo Libre')):
        doc.append(
            "El siguiente diagrama representa las condiciones de sujecion y las "
            "cargas externas aplicadas sobre la viga, tal como fueron definidas "
            "como datos de entrada del analisis.\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        if imagen_dcl and os.path.exists(imagen_dcl):
            with doc.create(Figure(position='H')) as fig:
                fig.add_image(imagen_dcl, width=NoEscape(r'0.92\textwidth'))
                fig.add_caption('Diagrama de cuerpo libre de la viga.')
        else:
            doc.append(NoEscape(
                r"\textit{Imagen no disponible: verifique la ruta de imagen\_dcl.}"
            ))

    # ══════════════════════════════════════════════════════════════════════════
    # § 2  PARAMETROS INICIALES
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Parametros Iniciales y Propiedades del Material')):
        doc.append(
            "Se presentan los parametros geometricos de la viga y las "
            "propiedades mecanicas del material seleccionado para el analisis.\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        _booktabs_table(
            doc,
            caption="Propiedades globales de la viga.",
            col_fmt="lcc",
            header_cells=["Variable / Parametro", "Valor", "Unidades"],
            rows=[
                [r"Longitud de la viga ($l$)",            f"{l:.2f}",              "m"],
                [r"Esfuerzo de fluencia ($S_y$)",          f"{Sy:.2f}",             "MPa"],
                [r"Factor de Seguridad ($FS$)",            f"{FS:.2f}",             "---"],
                [r"Esfuerzo admisible ($\sigma_{adm}$)",   f"{sigmaAllow_MPa:.2f}", "MPa"],
                [r"Grado de hiperestaticidad ($n$)",       str(n_dof),              "---"],
            ]
        )

    # ══════════════════════════════════════════════════════════════════════════
    # § 3  CONFIGURACION DE APOYOS
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Configuracion de Apoyos')):
        dof_desc = {1: "1 reaccion (Fy)", 2: "2 reacciones (Fy, M)"}
        doc.append(
            "La siguiente tabla resume la posicion y el tipo de cada apoyo "
            "definido en la viga. El grado de libertad restringido (DOF) indica "
            "el numero de incognitas que aporta cada apoyo al sistema de ecuaciones.\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        rows = []
        for key, sup in r.items():
            loc = sup.get('location', 0)
            typ = sup.get('type', '-')
            dof = sup.get('dof', 1)
            rows.append([key, f"{loc:.2f}", typ, dof_desc.get(dof, str(dof))])

        _booktabs_table(
            doc,
            caption="Detalle de los apoyos de la viga.",
            col_fmt="cccc",
            header_cells=["ID", "Ubicacion [m]", "Tipo", "Restricciones"],
            rows=rows
        )

    # ══════════════════════════════════════════════════════════════════════════
    # § 4  CARGAS EXTERNAS APLICADAS
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Cargas Externas Aplicadas')):
        doc.append(
            "Se listan todas las fuerzas y momentos externos actuantes sobre "
            "la viga. Las cargas distribuidas quedan definidas por sus posiciones "
            "de inicio ($a$) y fin ($a_1$).\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        unit_map = {
            typesloads[0]: "kN",
            typesloads[1]: "kN/m",
            typesloads[2]: "kN/m",
            typesloads[3]: "kN/m",
            typesloads[4]: "kN.m",
        }
        rows = []
        for key, load in f.items():
            typ    = load.get('type', '---')
            val    = load.get('value', 0.0)
            pos_a  = load.get('a', 0.0)
            pos_a1 = load.get('a1', '---')
            unidad = unit_map.get(typ, "---")
            a1_str = f"{pos_a1:.2f}" if isinstance(pos_a1, (int, float)) else str(pos_a1)
            rows.append([key, typ, f"{val:.2f}", f"{pos_a:.2f}", a1_str, unidad])

        _booktabs_table(
            doc,
            caption="Cargas externas aplicadas sobre la viga.",
            col_fmt="cllccc",
            header_cells=["ID", "Tipo de carga", "Magnitud", "$a$ [m]", "$a_1$ [m]", "Unidad"],
            rows=rows
        )

    # ══════════════════════════════════════════════════════════════════════════
    # § 5  PLANTEAMIENTO DEL SISTEMA DE ECUACIONES
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Planteamiento del Sistema de Ecuaciones')):
        doc.append(
            "El analisis se fundamenta en el metodo de funciones de singularidad "
            "(MacAulay). Las condiciones de equilibrio global junto con las "
            "condiciones de frontera cinematicas (deflexion nula y, en "
            "empotramiento, pendiente nula) constituyen el sistema de ecuaciones "
            "que permite resolver las reacciones desconocidas.\n"
        )
        doc.append(NoEscape(r'\vspace{8pt}'))

        with doc.create(Subsection('Ecuaciones de equilibrio')):
            doc.append(NoEscape(r'\vspace{4pt}'))
            doc.append(NoEscape(r"\textbf{Sumatoria de fuerzas en Y:}"))
            doc.append(NoEscape(r'\vspace{4pt}'))
            with doc.create(Alignat(numbering=False, escape=False)) as ag:
                ag.append(r"\sum F_y &= \sum_i R_{i,y} + \sum_j F_j = 0")
            doc.append(NoEscape(r'\vspace{6pt}'))
            doc.append(NoEscape(r"\textbf{Sumatoria de momentos respecto al origen:}"))
            doc.append(NoEscape(r'\vspace{4pt}'))
            with doc.create(Alignat(numbering=False, escape=False)) as ag:
                ag.append(r"\sum M_O &= \sum_i R_i \cdot x_i + \sum_j F_j \cdot a_j = 0")

        with doc.create(Subsection('Condiciones de frontera cinematicas')):
            doc.append(NoEscape(r'\vspace{4pt}'))
            bc_rows = []
            for k, sup in r.items():
                x   = sup['location']
                dof = sup['dof']
                bc_rows.append([
                    k, f"{x:.2f}",
                    r"$y(x) = 0$",
                    r"$\theta(x) = 0$" if dof == 2 else "---"
                ])

            _booktabs_table(
                doc,
                caption="Condiciones de frontera aplicadas.",
                col_fmt="cccc",
                header_cells=["Apoyo", "Posicion [m]", "Deflexion", "Pendiente"],
                rows=bc_rows
            )

    # ══════════════════════════════════════════════════════════════════════════
    # § 6  REACCIONES EN LOS APOYOS
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Reacciones en los Apoyos')):
        doc.append(
            "Resuelto el sistema de ecuaciones se obtienen las siguientes "
            "reacciones estaticas:\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        rows = []
        for name, data in r_sol.items():
            val  = data.get('value', 0.0)
            pos  = data.get('a', 0.0)
            tipo = data.get('type', '')
            unid = "kN" if tipo == typesloads[0] else "kN.m"
            sentido = "positivo" if val >= 0 else "negativo"
            rows.append([name, f"{pos:.2f}", f"{val:.4f}", unid, sentido])

        _booktabs_table(
            doc,
            caption="Reacciones estaticas calculadas.",
            col_fmt="ccccc",
            header_cells=["Reaccion", "Posicion [m]", "Valor", "Unidad", "Sentido"],
            rows=rows
        )

    # ══════════════════════════════════════════════════════════════════════════
    # § 7  VERIFICACION DE EQUILIBRIO
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Verificacion de Equilibrio')):
        doc.append(
            "Como control de calidad del resultado, se verifica que la "
            "sumatoria de fuerzas verticales y la sumatoria de momentos "
            "respecto al origen sean nulas, confirmando el equilibrio estatico "
            "del sistema.\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        sum_Fy, sum_M0, eq_rows = _equilibrium_check(r_sol, f, typesloads)

        _booktabs_table(
            doc,
            caption="Contribuciones individuales al equilibrio ($M$ respecto a $x=0$).",
            col_fmt="lcc",
            header_cells=["Elemento", "$F_y$ [kN]", "$M_O$ [kN.m]"],
            rows=eq_rows
        )

        doc.append(NoEscape(r'\vspace{10pt}'))

        tol = 1e-4
        ok_Fy = abs(sum_Fy) < tol
        ok_M  = abs(sum_M0) < tol
        c_Fy  = "okgreen"   if ok_Fy else "errred"
        c_M   = "okgreen"   if ok_M  else "errred"
        t_Fy  = "EQUILIBRADO" if ok_Fy else "ERROR"
        t_M   = "EQUILIBRADO" if ok_M  else "ERROR"

        doc.append(NoEscape(
            r"\begin{center}\small"
            rf"$\sum F_y = {sum_Fy:.2e}$ kN"
            rf" \quad $\Rightarrow$ \quad \textbf{{\textcolor{{{c_Fy}}}{{{t_Fy}}}}}"
            r"\qquad\qquad"
            r"\end{center}"
            
            r"\begin{center}\small"
            rf"$\sum M_O = {sum_M0:.2e}$ kN$\cdot$m"
            rf" \quad $\Rightarrow$ \quad \textbf{{\textcolor{{{c_M}}}{{{t_M}}}}}"
            r"\end{center}"
        ))

    # ══════════════════════════════════════════════════════════════════════════
    # § 8  DIAGRAMAS DE CORTANTE Y MOMENTO FLECTOR
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Diagramas de Fuerza Cortante y Momento Flector')):
        doc.append(
            "Los diagramas $V(x)$ y $M(x)$ se obtienen mediante la integracion "
            "numerica de las funciones de singularidad a lo largo del eje de la viga.\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        if imagen_diagramas and os.path.exists(imagen_diagramas):
            with doc.create(Figure(position='H')) as fig:
                fig.add_image(imagen_diagramas, width=NoEscape(r'0.80\textwidth'))
                fig.add_caption(r'Diagramas $V(x)$ y $M(x)$ a lo largo de la viga.')
        else:
            doc.append(NoEscape(
                r"\textit{Imagen no disponible: verifique la ruta de imagen\_diagramas.}"
            ))

        doc.append(NoEscape(r'\vspace{8pt}'))
        doc.append(NoEscape(
            r"El \textbf{momento flector maximo absoluto} registrado es "
            rf"\textbf{{$|M|_{{max}} = {Mmax:.2f}$ kN$\cdot$m}}."
        ))

    # ══════════════════════════════════════════════════════════════════════════
    # § 9  DISENO DE LA SECCION TRANSVERSAL
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Diseno de la Seccion Transversal')):
        doc.append(
            "A partir del momento flector maximo y del esfuerzo admisible "
            "se determina el modulo de seccion minimo requerido.\n"
        )
        doc.append(NoEscape(r'\vspace{6pt}'))

        with doc.create(Subsection('Esfuerzo admisible')):
            doc.append(NoEscape(r'\vspace{4pt}'))
            with doc.create(Alignat(numbering=False, escape=False)) as ag:
                ag.append(
                    r"\sigma_{adm} &= \frac{S_y}{FS} = "
                    rf"\frac{{{Sy:.0f}\,\text{{MPa}}}}{{{FS:.0f}}} = "
                    rf"{sigmaAllow_MPa:.2f}\,\text{{MPa}}"
                )

        doc.append(NoEscape(r'\vspace{4pt}'))

        with doc.create(Subsection('Modulo de seccion requerido')):
            doc.append(NoEscape(r'\vspace{4pt}'))
            with doc.create(Alignat(numbering=False, escape=False)) as ag:
                ag.append(r"s &= \frac{M_{max}}{\sigma_{adm}} \\")
                ag.append(
                    rf"s &= \frac{{{Mmax:.2f}\,\text{{kN}}\cdot\text{{m}}}}"
                    rf"{{{sigmaAllow_MPa:.2f} \times 10^3\,\text{{kN/m}}^2}} \\"
                )
                ag.append(
                    rf"s &= {s_m3:.6f}\,\text{{m}}^3 = "
                    rf"\boxed{{{s_cm3:.2f}\,\text{{cm}}^3}}"
                )

        doc.append(NoEscape(r'\vspace{10pt}'))
        doc.append(NoEscape(
            r"\noindent Con el valor de $s$ calculado se debe consultar el "
            r"catalogo de perfiles laminados (e.g.\ perfiles W, IPE, HEA) y "
            r"seleccionar el perfil cuyo modulo de seccion $S_x$ sea "
            r"\textbf{igual o inmediatamente superior} al valor requerido."
        ))

    # ══════════════════════════════════════════════════════════════════════════
    # § 10  RESUMEN EJECUTIVO
    # ══════════════════════════════════════════════════════════════════════════
    with doc.create(Section('Resumen Ejecutivo')):
        doc.append(
            "Se consolidan los resultados mas relevantes del analisis "
            "para una consulta rapida.\n"
        )
        doc.append(NoEscape(r'\vspace{8pt}'))

        _summary_box(doc, [
            ("Longitud de la viga",          rf"$l = {l:.2f}$ m"),
            ("Material / Norma",             rf"$S_y = {Sy:.0f}$ MPa"),
            ("Factor de seguridad",          rf"$FS = {FS:.1f}$"),
            ("Esfuerzo admisible",           rf"$\sigma_{{adm}} = {sigmaAllow_MPa:.2f}$ MPa"),
            ("Momento flector maximo",       rf"$|M|_{{max}} = {Mmax:.2f}$ kN$\cdot$m"),
            ("Modulo de seccion requerido",  rf"$s_{{req}} = {s_cm3:.2f}$ cm$^3$"),
            ("Grado de hiperestaticidad",    rf"$n = {n_dof}$ ecuaciones"),
        ])

        doc.append(NoEscape(r'\vspace{12pt}'))

        rows = []
        for name, data in r_sol.items():
            val  = data.get('value', 0.0)
            pos  = data.get('a', 0.0)
            tipo = data.get('type', '')
            unid = "kN" if tipo == typesloads[0] else "kN.m"
            rows.append([name, f"{pos:.2f}", f"{val:.3f}", unid])

        _booktabs_table(
            doc,
            caption="Tabla resumen de reacciones.",
            col_fmt="cccc",
            header_cells=["Reaccion", "Posicion [m]", "Valor", "Unidad"],
            rows=rows
        )

    # ══════════════════════════════════════════════════════════════════════════
    # GENERAR PDF
    # ══════════════════════════════════════════════════════════════════════════
    try:
        doc.generate_pdf(
            compiler='pdflatex',
            clean_tex=True,
            clean=True,
            filepath=ruta_completa
        )
        print(f"[OK] Reporte guardado en: {ruta_completa}.pdf")
    except Exception as e:
        doc.generate_tex(filepath=ruta_completa)
        print(
            f"[WARN] No se pudo compilar a PDF. "
            f"Archivo .tex guardado en: {ruta_completa}.tex\n"
            f"Error: {e}"
        )