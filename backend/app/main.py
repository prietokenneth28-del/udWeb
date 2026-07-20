from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from app.models import CicloAcademico, Semestre, Materia, HistorialAcademico, User
from app.database import get_session
from app.auth import router as auth_router, get_current_user

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Plan de Estudios API")

origenes_permitidos = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://prietokenneth28-del.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


def _materia_dict(materia: Materia) -> dict:
    return {
        "id": materia.id,
        "nombre": materia.nombre,
        "codigo": materia.codigo,
        "creditos": materia.creditos,
        "tipo": materia.tipo,
        "categoria": materia.categoria,
        "prereq": materia.prereq,
    }


@app.get("/api/plan-estudios")
def obtener_plan_estudios(session: Session = Depends(get_session)):
    ciclos = session.exec(select(CicloAcademico)).all()
    semestres = session.exec(select(Semestre)).all()
    materias = session.exec(select(Materia)).all()

    materias_por_semestre: dict[int, list] = {}
    for materia in materias:
        materias_por_semestre.setdefault(materia.semestre_id, []).append(materia)

    semestres_por_ciclo: dict[str, list] = {}
    for semestre in semestres:
        semestres_por_ciclo.setdefault(semestre.ciclo_id, []).append(semestre)

    resultado = []
    for ciclo in ciclos:
        semestres_ciclo = sorted(semestres_por_ciclo.get(ciclo.id, []), key=lambda s: s.numero)
        resultado.append({
            "id": ciclo.id,
            "nombre": ciclo.nombre,
            "semestres": [
                {
                    "numero": semestre.numero,
                    "materias": [_materia_dict(m) for m in materias_por_semestre.get(semestre.id, [])],
                }
                for semestre in semestres_ciclo
            ],
        })
    return resultado


@app.get("/api/historial", response_model=list[HistorialAcademico])
def obtener_historial(session: Session = Depends(get_session)):
    return session.exec(select(HistorialAcademico)).all()


@app.post("/api/historial", response_model=HistorialAcademico, status_code=201)
def crear_historial(
    registro: HistorialAcademico,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    materia = session.get(Materia, registro.materia_id)
    if not materia:
        raise HTTPException(status_code=404, detail="La materia no existe")

    registro.id = None
    session.add(registro)
    session.commit()
    session.refresh(registro)
    return registro


@app.put("/api/historial/{historial_id}", response_model=HistorialAcademico)
def actualizar_historial(
    historial_id: int,
    datos: HistorialAcademico,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    registro = session.get(HistorialAcademico, historial_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro de historial no encontrado")

    datos_dict = datos.model_dump(exclude={"id", "fecha_registro"})
    for clave, valor in datos_dict.items():
        setattr(registro, clave, valor)
    registro.fecha_registro = datetime.utcnow()
    session.add(registro)
    session.commit()
    session.refresh(registro)
    return registro


@app.delete("/api/historial/{historial_id}", status_code=204)
def eliminar_historial(
    historial_id: int,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    registro = session.get(HistorialAcademico, historial_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
    session.delete(registro)
    session.commit()


@app.get("/api/estadisticas")
def obtener_estadisticas(session: Session = Depends(get_session)):
    materias = session.exec(select(Materia)).all()
    historial = session.exec(select(HistorialAcademico)).all()

    creditos_totales = sum(m.creditos for m in materias)
    creditos_por_materia = {m.id: m.creditos for m in materias}

    creditos_aprobados = sum(
        creditos_por_materia.get(h.materia_id, 0)
        for h in historial
        if h.estado == "Aprobada"
    )

    registros_con_nota = [h for h in historial if h.nota_final is not None]
    suma_ponderada = sum(h.nota_final * creditos_por_materia.get(h.materia_id, 0) for h in registros_con_nota)
    creditos_con_nota = sum(creditos_por_materia.get(h.materia_id, 0) for h in registros_con_nota)
    papa = round(suma_ponderada / creditos_con_nota, 2) if creditos_con_nota else None

    porcentaje_avance = round((creditos_aprobados / creditos_totales) * 100, 1) if creditos_totales else 0

    return {
        "creditos_totales": creditos_totales,
        "creditos_aprobados": creditos_aprobados,
        "porcentaje_avance": porcentaje_avance,
        "papa": papa,
    }
