import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from sqlmodel import Session, select
from app.models import (
    CicloAcademico,
    Semestre,
    Materia,
    HistorialAcademico,
    User,
    SemestreHorario,
    SemestreHorarioCreate,
    ClaseHorario,
    ClaseHorarioCreate,
    Actividad,
    ActividadCreate,
)
from app.database import get_session
from app.auth import router as auth_router, get_current_user
from app.telegram_bot import (
    construir_mensaje_horario_hoy,
    enviar_mensaje_telegram,
    isoweekday_hoy,
    responder_actualizacion_telegram,
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Plan de Estudios API")

origenes_permitidos = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://prietokenneth28-del.github.io",
    "https://udweb-1-zkip.onrender.com",
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
def obtener_historial(
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
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


def _clase_dict(clase: ClaseHorario) -> dict:
    return {
        "id": clase.id,
        "dia": clase.dia,
        "horaInicio": clase.hora_inicio,
        "horaFin": clase.hora_fin,
        "materia": clase.materia,
        "color": clase.color,
        "aula": clase.aula,
    }


@app.get("/api/horario")
def obtener_horario(
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    semestres = session.exec(select(SemestreHorario)).all()
    clases = session.exec(select(ClaseHorario)).all()

    clases_por_semestre: dict[int, list] = {}
    for clase in clases:
        clases_por_semestre.setdefault(clase.semestre_numero, []).append(clase)

    return {
        "semesters": {
            str(semestre.numero): {
                "label": semestre.label,
                "classes": [_clase_dict(c) for c in clases_por_semestre.get(semestre.numero, [])],
            }
            for semestre in semestres
        }
    }


@app.post("/api/horario/semestres", status_code=201)
def crear_semestre_horario(
    datos: SemestreHorarioCreate,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    if session.get(SemestreHorario, datos.numero):
        raise HTTPException(status_code=400, detail="Ese semestre ya existe")
    semestre = SemestreHorario(numero=datos.numero, label=datos.label)
    session.add(semestre)
    session.commit()
    session.refresh(semestre)
    return semestre


@app.delete("/api/horario/semestres/{numero}", status_code=204)
def eliminar_semestre_horario(
    numero: int,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    semestre = session.get(SemestreHorario, numero)
    if not semestre:
        raise HTTPException(status_code=404, detail="Semestre no encontrado")

    clases = session.exec(select(ClaseHorario).where(ClaseHorario.semestre_numero == numero)).all()
    for clase in clases:
        session.delete(clase)
    session.delete(semestre)
    session.commit()


@app.post("/api/horario/clases", status_code=201)
def crear_clase_horario(
    datos: ClaseHorarioCreate,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    if not session.get(SemestreHorario, datos.semestre_numero):
        raise HTTPException(status_code=404, detail="El semestre no existe")

    clase = ClaseHorario(**datos.model_dump())
    session.add(clase)
    session.commit()
    session.refresh(clase)
    return _clase_dict(clase)


@app.put("/api/horario/clases/{clase_id}")
def actualizar_clase_horario(
    clase_id: int,
    datos: ClaseHorarioCreate,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    clase = session.get(ClaseHorario, clase_id)
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    if not session.get(SemestreHorario, datos.semestre_numero):
        raise HTTPException(status_code=404, detail="El semestre no existe")

    for clave, valor in datos.model_dump().items():
        setattr(clase, clave, valor)
    session.add(clase)
    session.commit()
    session.refresh(clase)
    return _clase_dict(clase)


@app.delete("/api/horario/clases/{clase_id}", status_code=204)
def eliminar_clase_horario(
    clase_id: int,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    clase = session.get(ClaseHorario, clase_id)
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    session.delete(clase)
    session.commit()


@app.post("/api/horario/notificar-hoy")
def notificar_horario_hoy(
    x_bot_secret: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    secreto_esperado = os.getenv("TELEGRAM_NOTIFY_SECRET")
    if not secreto_esperado or x_bot_secret != secreto_esperado:
        raise HTTPException(status_code=403, detail="Secreto inválido")

    mensaje = construir_mensaje_horario_hoy(session, isoweekday_hoy())
    enviar_mensaje_telegram(mensaje)
    return {"status": "enviado", "mensaje": mensaje}


@app.get("/api/horario/debug")
def debug_horario(
    x_bot_secret: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    secreto_esperado = os.getenv("TELEGRAM_NOTIFY_SECRET")
    if not secreto_esperado or x_bot_secret != secreto_esperado:
        raise HTTPException(status_code=403, detail="Secreto inválido")

    semestres = session.exec(select(SemestreHorario)).all()
    clases = session.exec(select(ClaseHorario)).all()

    return {
        "dia_hoy_isoweekday": isoweekday_hoy(),
        "semestre_activo_env": os.getenv("HORARIO_SEMESTRE_ACTIVO"),
        "semestres_registrados": [{"numero": s.numero, "label": s.label} for s in semestres],
        "clases": [
            {
                "id": c.id,
                "semestre_numero": c.semestre_numero,
                "dia": c.dia,
                "materia": c.materia,
                "hora_inicio": c.hora_inicio,
                "hora_fin": c.hora_fin,
            }
            for c in clases
        ],
    }


@app.post("/api/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    secreto_esperado = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if secreto_esperado and x_telegram_bot_api_secret_token != secreto_esperado:
        raise HTTPException(status_code=403, detail="Secreto inválido")

    update = await request.json()
    responder_actualizacion_telegram(session, update)
    return {"ok": True}


@app.get("/api/actividades", response_model=list[Actividad])
def obtener_actividades(
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    return session.exec(select(Actividad)).all()


@app.post("/api/actividades", response_model=Actividad, status_code=201)
def crear_actividad(
    datos: ActividadCreate,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    actividad = Actividad(**datos.model_dump())
    session.add(actividad)
    session.commit()
    session.refresh(actividad)
    return actividad


@app.put("/api/actividades/{actividad_id}", response_model=Actividad)
def actualizar_actividad(
    actividad_id: int,
    datos: ActividadCreate,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    actividad = session.get(Actividad, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    for clave, valor in datos.model_dump().items():
        setattr(actividad, clave, valor)
    session.add(actividad)
    session.commit()
    session.refresh(actividad)
    return actividad


@app.delete("/api/actividades/{actividad_id}", status_code=204)
def eliminar_actividad(
    actividad_id: int,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    actividad = session.get(Actividad, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    session.delete(actividad)
    session.commit()


@app.get("/api/estadisticas")
def obtener_estadisticas(
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
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
