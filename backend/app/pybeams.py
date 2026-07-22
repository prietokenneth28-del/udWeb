import base64
import os
import sys
from typing import Literal, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User

# ── Hacer importables los módulos de backend/pyBeams (no son un paquete) ─────
PYBEAMS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyBeams")
if PYBEAMS_DIR not in sys.path:
    sys.path.insert(0, PYBEAMS_DIR)

from discontinousFunction import numericalDiscontinousFuctions  # noqa: E402
from matrixSolution import sumFY, sumM, singularityEq, solveEquation  # noqa: E402
from extraValidation import loadValidation  # noqa: E402
from grafication import plot_shear_moment, plot_free_body_diagram  # noqa: E402
from report_reportlab import generar_reporte_pdf_bytes  # noqa: E402

router = APIRouter(prefix="/api/pybeams", tags=["pybeams"])

TYPES_LOADS = [
    "Point load",
    "Uniformly distributed",
    "Triangular distributed 1",
    "Triangular distributed 2",
    "Moment load",
]

TYPES_SUPPORT_DOF = {"Roller": 1, "Pinned": 1, "Fixed": 2}


class SupportInput(BaseModel):
    location: float
    type: Literal["Roller", "Pinned", "Fixed"]


class LoadInput(BaseModel):
    value: float
    a: float
    a1: Optional[float] = None
    type: Literal[
        "Point load",
        "Uniformly distributed",
        "Triangular distributed 1",
        "Triangular distributed 2",
        "Moment load",
    ]


class BeamRequest(BaseModel):
    l: float
    Sy: float
    FS: float
    supports: dict[str, SupportInput]
    loads: dict[str, LoadInput]


class ReactionResult(BaseModel):
    value: float
    location: float
    type: str


class BeamResponse(BaseModel):
    reactions: dict[str, ReactionResult]
    Mmax: float
    required_section_modulus_cm3: float
    diagrams: dict[str, str]


def _solve_beam(l: float, r: dict, f: dict):
    v, M, theta, y, loadEq, MomentEq = numericalDiscontinousFuctions(f, l, TYPES_LOADS)

    unknowns = []
    for key, support in r.items():
        unknowns.append({"name": f"{key}y", "location": support["location"], "kind": "force"})
        if support["dof"] == 2:
            unknowns.append({"name": f"M{key}", "location": support["location"], "kind": "moment"})

    sumForces = sumFY(unknowns)
    totalMoments, sumMoment = sumM(unknowns, MomentEq, loadEq)

    # Las constantes de integración C1/C2 de la curva de deflexión siempre están
    # presentes como incógnitas, así que las ecuaciones de frontera (deflexión/
    # pendiente nula en cada apoyo) siempre son necesarias para cerrar el sistema,
    # sea la viga estáticamente determinada o indeterminada.
    sumSingularity, total_y = singularityEq(unknowns, r, f, TYPES_LOADS)

    _, r_sol = solveEquation(sumForces, sumMoment, sumSingularity, loadEq, totalMoments, total_y, unknowns)

    r_v, r_M, r_theta, r_y, r_loadEq, r_MomentEq = numericalDiscontinousFuctions(r_sol, l, TYPES_LOADS)
    v = v + r_v
    M = M + r_M

    Mmax = max(abs(M.min()), M.max())
    return Mmax, r_sol, v, M


def _beam_geometry(Mmax: float, Sy: float, FS: float) -> float:
    sigma_allow = Sy * 1000 / FS  # [kPa]
    s = Mmax / sigma_allow  # [m3]
    return s * 100**3  # [cm3]


def _resolver_solicitud(datos: BeamRequest):
    if not datos.supports:
        raise HTTPException(status_code=400, detail="Se requiere al menos un apoyo")
    if not datos.loads:
        raise HTTPException(status_code=400, detail="Se requiere al menos una carga")

    r = {
        key: {
            "location": support.location,
            "dof": TYPES_SUPPORT_DOF[support.type],
            "type": support.type,
        }
        for key, support in datos.supports.items()
    }
    f = {
        key: {
            "value": load.value,
            "a": load.a,
            "a1": load.a1 if load.a1 is not None else 0,
            "type": load.type,
        }
        for key, load in datos.loads.items()
    }

    try:
        loadValidation(f, TYPES_LOADS, datos.l)
        Mmax, r_sol, v, M = _solve_beam(datos.l, r, f)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except np.linalg.LinAlgError:
        raise HTTPException(
            status_code=400,
            detail="El sistema de apoyos definido no es estable (mecanismo o restricciones redundantes mal ubicadas)",
        )

    s = _beam_geometry(Mmax, datos.Sy, datos.FS)
    return r, f, Mmax, r_sol, v, M, s


@router.post("/calcular", response_model=BeamResponse)
def calcular_viga(
    datos: BeamRequest,
    usuario_actual: User = Depends(get_current_user),
):
    r, f, Mmax, r_sol, v, M, s = _resolver_solicitud(datos)

    shear_moment_png = plot_shear_moment(v.flatten(), M.flatten(), datos.l, return_bytes=True)
    free_body_png = plot_free_body_diagram(r, f, TYPES_LOADS, datos.l, return_bytes=True)

    return BeamResponse(
        reactions={
            name: ReactionResult(
                value=round(data["value"], 3),
                location=data["a"],
                type=data["type"],
            )
            for name, data in r_sol.items()
        },
        Mmax=round(Mmax, 3),
        required_section_modulus_cm3=round(s, 3),
        diagrams={
            "shear_moment": base64.b64encode(shear_moment_png).decode("ascii"),
            "free_body": base64.b64encode(free_body_png).decode("ascii"),
        },
    )


@router.post("/reporte")
def descargar_reporte(
    datos: BeamRequest,
    usuario_actual: User = Depends(get_current_user),
):
    r, f, Mmax, r_sol, v, M, s = _resolver_solicitud(datos)

    shear_moment_png = plot_shear_moment(v.flatten(), M.flatten(), datos.l, return_bytes=True)
    free_body_png = plot_free_body_diagram(r, f, TYPES_LOADS, datos.l, return_bytes=True)

    pdf_bytes = generar_reporte_pdf_bytes(
        datos.l, datos.Sy, datos.FS, r_sol, r, f, Mmax, s, TYPES_LOADS,
        imagen_dcl_bytes=free_body_png,
        imagen_diagramas_bytes=shear_moment_png,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="reporte_viga.pdf"'},
    )
