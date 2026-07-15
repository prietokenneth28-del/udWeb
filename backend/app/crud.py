"""
Operaciones sobre la base de datos. Mantener esta lógica separada de
main.py hace más fácil probarla o reutilizarla desde otro lugar
(un script, un job programado, etc.).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas

# Nota que se considera aprobatoria (escala 0.0 - 5.0, estándar en
# Colombia). Si tu universidad usa otra escala/umbral, cambia esta
# constante — todo lo demás se ajusta solo.
NOTA_APROBATORIA = 3.0


def _estado_para_nota(nota_final: float | None) -> str:
    if nota_final is None:
        return "En curso"
    return "Aprobada" if nota_final >= NOTA_APROBATORIA else "Reprobada"


# --- Plan de estudios (solo lectura) --------------------------------------

def get_plan_estudios(db: Session) -> list[models.CicloAcademico]:
    stmt = (
        select(models.CicloAcademico)
        .options(
            selectinload(models.CicloAcademico.semestres).selectinload(
                models.Semestre.materias
            )
        )
        .order_by(models.CicloAcademico.id)
    )
    return list(db.scalars(stmt).all())


# --- Historial académico --------------------------------------------------

def get_historial(db: Session) -> list[models.HistorialAcademico]:
    stmt = (
        select(models.HistorialAcademico)
        .options(selectinload(models.HistorialAcademico.materia))
        .order_by(models.HistorialAcademico.fecha_registro.desc())
    )
    return list(db.scalars(stmt).all())


def get_historial_by_id(db: Session, historial_id: int) -> models.HistorialAcademico | None:
    return db.get(models.HistorialAcademico, historial_id)


def create_historial(
    db: Session, data: schemas.HistorialCreate
) -> models.HistorialAcademico:
    registro = models.HistorialAcademico(
        materia_id=data.materia_id,
        periodo=data.periodo,
        nota_final=data.nota_final,
        estado=_estado_para_nota(data.nota_final),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def update_historial(
    db: Session, registro: models.HistorialAcademico, data: schemas.HistorialUpdate
) -> models.HistorialAcademico:
    if data.periodo is not None:
        registro.periodo = data.periodo
    if data.nota_final is not None:
        registro.nota_final = data.nota_final
        registro.estado = _estado_para_nota(data.nota_final)
    db.commit()
    db.refresh(registro)
    return registro


# --- Estadísticas / PAPA ---------------------------------------------------

def get_estadisticas(db: Session) -> schemas.EstadisticasOut:
    ciclos = get_plan_estudios(db)
    historial = get_historial(db)

    # id de materia -> mejor registro de historial (si una materia se
    # repitió, nos quedamos con la más reciente para créditos/avance)
    ultimo_registro_por_materia: dict[int, models.HistorialAcademico] = {}
    for h in sorted(historial, key=lambda h: h.fecha_registro):
        ultimo_registro_por_materia[h.materia_id] = h

    creditos_totales = 0.0
    creditos_aprobados = 0.0
    desglose: dict[str, schemas.DesgloseCiclo] = {}

    suma_ponderada = 0.0
    creditos_evaluados = 0.0  # créditos de materias con nota (aprobadas o reprobadas)
    materias_cursadas = 0

    for ciclo in ciclos:
        tot_ciclo = 0.0
        aprob_ciclo = 0.0
        for semestre in ciclo.semestres:
            for materia in semestre.materias:
                tot_ciclo += materia.creditos
                registro = ultimo_registro_por_materia.get(materia.id)
                if registro and registro.estado == "Aprobada":
                    aprob_ciclo += materia.creditos
                if registro and registro.nota_final is not None:
                    suma_ponderada += float(registro.nota_final) * materia.creditos
                    creditos_evaluados += materia.creditos
                    materias_cursadas += 1
        creditos_totales += tot_ciclo
        creditos_aprobados += aprob_ciclo
        desglose[ciclo.nombre] = schemas.DesgloseCiclo(
            creditos_totales=tot_ciclo, creditos_aprobados=aprob_ciclo
        )

    porcentaje = round((creditos_aprobados / creditos_totales) * 100, 1) if creditos_totales else 0.0
    papa = round(suma_ponderada / creditos_evaluados, 2) if creditos_evaluados else None

    return schemas.EstadisticasOut(
        creditos_totales=creditos_totales,
        creditos_aprobados=creditos_aprobados,
        creditos_pendientes=creditos_totales - creditos_aprobados,
        porcentaje_avance=porcentaje,
        papa=papa,
        materias_cursadas=materias_cursadas,
        desglose_por_ciclo=desglose,
    )
