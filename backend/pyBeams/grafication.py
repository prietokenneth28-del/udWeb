# grafication.py
# Generación y visualización de los diagramas estructurales utilizando Matplotlib.
#
# Uso desde linea de comandos:
# N/A. Se importa como módulo: from grafication import plot_shear_moment, plot_free_body_diagram
#
# Flujo:
# 1. Recibe los vectores de resultados (cortante, momento) y parámetros físicos.
# 2. Configura los subplots y ejes coordenados.
# 3. Dibuja apoyos, cargas y acotaciones para el Diagrama de Cuerpo Libre.
# 4. Traza las curvas y rellena áreas para los diagramas de fuerzas internas.
# 5. Exporta las imágenes a disco para su posterior uso en reportes.

import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches
import os

def plot_shear_moment(v, M, l, xMax=None, return_bytes=False):
    """
    Genera los diagramas de fuerza cortante y momento flector.

    Args:
        L (array): Vector de posiciones a lo largo de la viga (eje x).
        v (array): Vector de valores de fuerza cortante.
        M (array): Vector de valores de momento flector.
        l (float): Longitud total de la viga.
        xMax (float, opcional): Posición x donde el momento es máximo o el cortante es cero.
        return_bytes (bool, opcional): Si es True, retorna el PNG como bytes en vez de escribirlo a disco.
    """
    size = round(l / 0.01 + 1)
    L = np.linspace(0, l, size)

    # tiledlayout(2,1) equivalente  en matplotlib
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    fig.tight_layout(pad=5.0)

    # ---------------------------------------------------------
    # 1. Diagrama de fuerza cortante (nexttile 1)
    # ---------------------------------------------------------
    axs[0].plot(L, v, color='black', linewidth=3)
    
    if xMax is not None:
        axs[0].axvline(x=xMax, color='red', linestyle='--', linewidth=2) # xline(xMax, "r--")
        
    axs[0].axvline(x=0, color='black', linewidth=2) # xline(0)
    axs[0].axhline(y=0, color='black', linewidth=2) # yline(0)
    
    # area(L,v,...) equivalente usando fill_between
    axs[0].fill_between(L, v, 0, color="#0072BD", alpha=0.8) 
    
    axs[0].set_title('Diagrama de Fuerza cortante', fontsize=14)
    axs[0].set_xlabel('x [m]', fontsize=12)
    axs[0].set_ylabel('V [kN]', fontsize=12)
    axs[0].set_xlim([-0.5, l + 1])
    axs[0].grid(True) # grid on

    # ---------------------------------------------------------
    # 2. Diagrama de momento flector (nexttile 2)
    # ---------------------------------------------------------
    axs[1].plot(L, M, color='black', linewidth=4)
    
    if xMax is not None:
        axs[1].axvline(x=xMax, color='red', linestyle='--', linewidth=2)
        
    axs[1].axvline(x=0, color='black', linewidth=2)
    axs[1].axhline(y=0, color='black', linewidth=2)
    
    # area(L,M,...) equivalente
    axs[1].fill_between(L, M, 0, color="#D44E14", alpha=0.8)
    
    axs[1].set_title('Diagrama de Momento flector', fontsize=14)
    axs[1].set_xlabel('x [m]', fontsize=12)
    axs[1].set_ylabel('M [kN.m]', fontsize=12)
    axs[1].set_xlim([-0.5, l + 1])
    axs[1].grid(True)

    plt.tight_layout()

    if return_bytes:
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", dpi=300)
        plt.close(fig)
        return buffer.getvalue()

    os.makedirs('report', exist_ok=True)
    ruta_completa = os.path.join('report', 'diagramas_viga.png')
    plt.savefig(ruta_completa, dpi=300)
    plt.close(fig)


def plot_free_body_diagram(r, f, typesloads, l, filename="diagrama_cuerpo_libre.png", return_bytes=False):
    """
    Genera el diagrama de cuerpo libre de la viga con sus apoyos y cargas aplicadas.

    Args:
        r   (dict):  Diccionario de apoyos con 'location', 'dof' y 'type'.
        f   (dict):  Diccionario de cargas con 'value', 'a', 'a1' y 'type'.
        typesloads (list): Lista de tipos de carga reconocidos por el sistema.
        l   (float): Longitud total de la viga [m].
        filename (str): Nombre del archivo PNG de salida.
        return_bytes (bool, opcional): Si es True, retorna el PNG como bytes en vez de escribirlo a disco.

    Apoyos soportados:
        - Fixed  (dof=2): empotrado, dibuja un rectángulo con rayado.
        - Pinned (dof=1, 'Pinned'): articulado, dibuja un triángulo con suelo.
        - Roller (dof=1, 'Roller'): rodillo, dibuja triángulo + círculos + suelo.

    Cargas soportadas:
        - typesloads[0] Point load              : flecha puntual vertical.
        - typesloads[1] Uniformly distributed   : bloque de flechas + línea superior.
        - typesloads[2] Triangular distributed 1: triángulo creciente (a → a1).
        - typesloads[3] Triangular distributed 2: triángulo decreciente (a → a1).
        - typesloads[4] Moment load             : arco curvo con flecha.
    """
    fig, ax = plt.subplots(figsize=(max(10, l * 0.7), 5))
    ax.set_xlim(-l * 0.08, l * 1.12)
    ax.set_ylim(-l * 0.20, l * 0.35)
    ax.set_aspect('equal')
    ax.axis('off')

    # ── Escala auxiliar ──────────────────────────────────────────────────
    beam_y   = 0.0
    beam_h   = l * 0.018          # grosor visual de la viga
    load_h   = l * 0.10           # altura de referencia para cargas
    sup_size = l * 0.055          # tamaño base de los símbolos de apoyo

    # ── 1. VIGA ──────────────────────────────────────────────────────────
    beam = plt.Rectangle((0, beam_y - beam_h / 2), l, beam_h,
                          color='#2C2C2A', zorder=3)
    ax.add_patch(beam)

    # ── 2. APOYOS ────────────────────────────────────────────────────────
    for key, support in r.items():
        x   = support['location']
        typ = support['type']

        if typ == "Fixed":
            # Rectángulo rayado pegado al extremo de la viga
            wall_w = sup_size * 0.7
            wall_h = sup_size * 2.2
            side   = -1 if x == 0 else 1      # izquierda o derecha
            wx     = x - wall_w if side == 1 else x

            wall = plt.Rectangle((wx, beam_y - wall_h / 2), wall_w, wall_h,
                                  facecolor='#D3D1C7', edgecolor='#444441',
                                  linewidth=1.2, zorder=2)
            ax.add_patch(wall)

            # Rayado diagonal
            n_lines = 6
            for i in range(n_lines + 1):
                yt = beam_y - wall_h / 2 + i * wall_h / n_lines
                ax.plot([wx - sup_size * 0.25, wx],
                        [yt - sup_size * 0.25, yt],
                        color='#888780', linewidth=0.8, zorder=2)

            # Línea exterior del muro
            outer_x = wx - sup_size * 0.25 if side == -1 else wx + wall_w + sup_size * 0.25
            ax.plot([outer_x, outer_x],
                    [beam_y - wall_h / 2, beam_y + wall_h / 2],
                    color='#444441', linewidth=1.5, zorder=2)

        elif typ in ("Roller", "Pinned"):
            # Triángulo
            tri_h = sup_size
            tri_pts = np.array([
                [x,              beam_y - beam_h / 2],
                [x - tri_h * 0.6, beam_y - beam_h / 2 - tri_h],
                [x + tri_h * 0.6, beam_y - beam_h / 2 - tri_h],
            ])
            triangle = plt.Polygon(tri_pts, closed=True,
                                   facecolor='none', edgecolor='#2C2C2A',
                                   linewidth=1.5, zorder=2)
            ax.add_patch(triangle)

            ground_y = beam_y - beam_h / 2 - tri_h

            if typ == "Roller":
                # Círculos rodantes
                r_circ = sup_size * 0.14
                for cx in [x - tri_h * 0.35, x, x + tri_h * 0.35]:
                    circle = plt.Circle((cx, ground_y - r_circ),
                                        r_circ, facecolor='none',
                                        edgecolor='#2C2C2A', linewidth=1.2, zorder=2)
                    ax.add_patch(circle)
                ground_y -= r_circ * 2

            # Línea de suelo + rayado
            ax.plot([x - tri_h * 0.8, x + tri_h * 0.8],
                    [ground_y, ground_y], color='#2C2C2A', linewidth=1.5, zorder=2)
            n_hatch = 7
            for i in range(n_hatch):
                hx = x - tri_h * 0.7 + i * (tri_h * 1.4 / (n_hatch - 1))
                ax.plot([hx, hx - sup_size * 0.2],
                        [ground_y, ground_y - sup_size * 0.2],
                        color='#888780', linewidth=0.8, zorder=2)

        # Etiqueta del apoyo
        ax.text(x, beam_y - sup_size * 2.2, f"{key}\n({typ})\nx={x} m",
                ha='center', va='top', fontsize=7.5,
                color='#3d3d3a', zorder=5)

    # ── 3. CARGAS ─────────────────────────────────────────────────────────
    arrow_kw = dict(arrowstyle='->', color='#185FA5',
                    lw=1.4, mutation_scale=12)

    for key, load in f.items():
        val  = load['value']
        a    = load['a']
        a1   = load.get('a1', a)
        ltyp = load['type']
        sign = np.sign(val) if val != 0 else -1   # negativo = hacia abajo

        label_color = '#185FA5'

        # ── Carga puntual ──
        if ltyp == typesloads[0]:
            arrow_start = beam_y + (load_h if sign < 0 else -load_h)
            arrow_end   = beam_y + (beam_h / 2 * np.sign(-sign))
            ax.annotate("", xy=(a, arrow_end), xytext=(a, arrow_start),
                        arrowprops=arrow_kw, zorder=4)
            ax.text(a, arrow_start + load_h * 0.25 * (-sign),
                    f"{abs(val)} kN", ha='center', va='center',
                    fontsize=8, color=label_color, fontweight='bold', zorder=5)

        # ── Carga distribuida uniforme ──
        elif ltyp == typesloads[1]:
            load_top = beam_y + load_h if sign < 0 else beam_y - load_h
            ax.plot([a, a1], [load_top, load_top],
                    color='#185FA5', linewidth=1.4, zorder=4)

            n_arrows = max(3, int((a1 - a) / (l * 0.08)) + 1)
            for xi in np.linspace(a, a1, n_arrows):
                ax.annotate("", xy=(xi, beam_y + beam_h / 2 * np.sign(-sign)),
                            xytext=(xi, load_top),
                            arrowprops=arrow_kw, zorder=4)

            mid = (a + a1) / 2
            ax.text(mid, load_top + load_h * 0.18 * (-sign),
                    f"q = {abs(val)} kN/m", ha='center', va='center',
                    fontsize=8, color=label_color, fontweight='bold', zorder=5)

        # ── Carga triangular creciente (tipo 2: 0 en a, máx en a1) ──
        elif ltyp == typesloads[2]:
            load_top   = beam_y + load_h * np.sign(-sign)
            beam_edge  = beam_y + beam_h / 2 * np.sign(-sign)
            n_arrows   = max(3, int((a1 - a) / (l * 0.08)) + 1)
            xs         = np.linspace(a, a1, n_arrows)
            fracs      = np.linspace(0, 1, n_arrows)
            tips       = beam_edge + (load_top - beam_edge) * fracs

            top_pts = [(xi, ti) for xi, ti in zip(xs, tips)]
            ax.plot([p[0] for p in top_pts], [p[1] for p in top_pts],
                    color='#185FA5', linewidth=1.4, zorder=4)
            ax.plot([a, a], [beam_edge, beam_edge], 'o',
                    color='#185FA5', markersize=4, zorder=4)

            for xi, ti in zip(xs, tips):
                if abs(ti - beam_edge) > load_h * 0.05:
                    ax.annotate("", xy=(xi, beam_edge), xytext=(xi, ti),
                                arrowprops=arrow_kw, zorder=4)

            mid = (a + a1) / 2
            ax.text(mid, load_top + load_h * 0.18 * (-sign),
                    f"{abs(val)} kN/m", ha='center', va='center',
                    fontsize=8, color=label_color, fontweight='bold', zorder=5)

        # ── Carga triangular decreciente (tipo 3: máx en a, 0 en a1) ──
        elif ltyp == typesloads[3]:
            load_top  = beam_y + load_h * np.sign(-sign)
            beam_edge = beam_y + beam_h / 2 * np.sign(-sign)
            n_arrows  = max(3, int((a1 - a) / (l * 0.08)) + 1)
            xs        = np.linspace(a, a1, n_arrows)
            fracs     = np.linspace(1, 0, n_arrows)
            tips      = beam_edge + (load_top - beam_edge) * fracs

            top_pts = [(xi, ti) for xi, ti in zip(xs, tips)]
            ax.plot([p[0] for p in top_pts], [p[1] for p in top_pts],
                    color='#185FA5', linewidth=1.4, zorder=4)
            ax.plot([a1, a1], [beam_edge, beam_edge], 'o',
                    color='#185FA5', markersize=4, zorder=4)

            for xi, ti in zip(xs, tips):
                if abs(ti - beam_edge) > load_h * 0.05:
                    ax.annotate("", xy=(xi, beam_edge), xytext=(xi, ti),
                                arrowprops=arrow_kw, zorder=4)

            mid = (a + a1) / 2
            ax.text(mid, load_top + load_h * 0.18 * (-sign),
                    f"{abs(val)} kN/m", ha='center', va='center',
                    fontsize=8, color=label_color, fontweight='bold', zorder=5)

        # ── Momento puntual ──
        elif ltyp == typesloads[4]:
            radius  = sup_size * 0.9
            theta1, theta2 = (30, 330) if val > 0 else (210, 510)
            arc = matplotlib.patches.Arc((a, beam_y), radius * 2, radius * 2,
                                         angle=0, theta1=theta1, theta2=theta2,
                                         color='#D85A30', linewidth=1.5, zorder=4)
            ax.add_patch(arc)

            # Cabeza de flecha del arco
            ang_rad = np.radians(theta2 if val > 0 else theta1)
            tip_x = a + radius * np.cos(ang_rad)
            tip_y = beam_y + radius * np.sin(ang_rad)
            d_ang  = np.radians(10) * (1 if val > 0 else -1)
            ax.annotate("", xy=(tip_x, tip_y),
                        xytext=(a + radius * np.cos(ang_rad - d_ang),
                                beam_y + radius * np.sin(ang_rad - d_ang)),
                        arrowprops=dict(arrowstyle='->', color='#D85A30',
                                        lw=1.4, mutation_scale=12), zorder=4)

            ax.text(a, beam_y + radius * 1.5,
                    f"M = {abs(val)} kN·m", ha='center', va='bottom',
                    fontsize=8, color='#D85A30', fontweight='bold', zorder=5)

    # ── 4. COTAS HORIZONTALES ─────────────────────────────────────────────
    cota_y = beam_y - sup_size * 3.0

    def draw_dim(ax, x1, x2, y, label, dy_label=0.018 * l):
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle='<->', color='#5F5E5A',
                                   lw=0.9, mutation_scale=8), zorder=3)
        ax.text((x1 + x2) / 2, y - dy_label, label,
                ha='center', va='top', fontsize=7.5, color='#5F5E5A', zorder=5)

    # Cota total de la viga
    draw_dim(ax, 0, l, cota_y, f"L = {l} m")

    # Cotas de inicio de cada carga distribuida (si a > 0)
    drawn_points = {0, l}
    for key, load in f.items():
        a  = load['a']
        a1 = load.get('a1', a)
        if a not in drawn_points and a > 0:
            draw_dim(ax, 0, a, cota_y - l * 0.06, f"{a} m")
            drawn_points.add(a)
        if a1 not in drawn_points and a1 < l and a1 != a:
            draw_dim(ax, a, a1, cota_y - l * 0.06, f"{a1 - a} m")
            drawn_points.add(a1)

    # ── 5. EJE X ──────────────────────────────────────────────────────────
    ax.annotate("", xy=(l * 1.07, beam_y), xytext=(-l * 0.03, beam_y),
                arrowprops=dict(arrowstyle='->', color='#888780',
                                lw=0.8, mutation_scale=8), zorder=1)
    ax.text(l * 1.09, beam_y, "x", ha='left', va='center',
            fontsize=9, color='#888780', zorder=5)

    # ── 6. TÍTULO ─────────────────────────────────────────────────────────

    
    plt.tight_layout()

    if return_bytes:
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", dpi=300, bbox_inches='tight')
        plt.close(fig)
        return buffer.getvalue()

    os.makedirs('report', exist_ok=True)
    ruta_completa = os.path.join('report', filename)
    plt.savefig(ruta_completa, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Diagrama de cuerpo libre guardado como '{filename}'")