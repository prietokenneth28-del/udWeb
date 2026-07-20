# Script de seed para el horario de clases. Corre con:
#   python seed_schedule.py
# (dentro del venv, con la migración de Alembic aplicada). Es IDEMPOTENTE:
# si el semestre o la clase ya existen, no se duplican.

from sqlmodel import Session, select
from app.database import engine
from app.models import SemestreHorario, ClaseHorario

SEMESTRES = [
    (7, "Semestre 7 (2026-2)"),
    (8, "Semestre 8"),
    (9, "Semestre 9"),
]

# (semestre, dia, horaInicio, horaFin, materia, color, aula)
CLASES = [
    (7, 6, 10, 12, "DISEÑO POR ELEMENTOS FINITOS", "bg-primary", None),
    (7, 6, 12, 14, "DISEÑO POR ELEMENTOS FINITOS", "bg-primary", None),
    (7, 6, 14, 16, "CÁTEDRA DE CONTEXTO", "bg-secondary", None),
    (7, 6, 16, 18, "CÁTEDRA DE CONTEXTO", "bg-secondary", None),
    (7, 1, 18, 20, "TERMODINÁMICA APLICADA", "bg-success", None),
    (7, 2, 18, 20, "PRODUCCIÓN DE TEXTOS CIENTÍFICOS", "bg-secondary", None),
    (7, 3, 18, 20, "TERMODINÁMICA APLICADA", "bg-success", None),
    (7, 4, 18, 20, "ASEGURAMIENTO METROLÓGICO", "bg-warning", None),
    (7, 1, 20, 22, "PRODUCCIÓN DE TEXTOS CIENTÍFICOS", "bg-secondary", None),
    (7, 2, 20, 22, "PROBABILIDAD Y ESTADÍSTICA", "bg-danger", None),
    (7, 3, 20, 22, "ASEGURAMIENTO METROLÓGICO", "bg-warning", None),
    (7, 5, 20, 22, "PROBABILIDAD Y ESTADÍSTICA", "bg-danger", None),
]


def main():
    with Session(engine) as session:
        semestres_insertados = 0
        for numero, label in SEMESTRES:
            if not session.get(SemestreHorario, numero):
                session.add(SemestreHorario(numero=numero, label=label))
                semestres_insertados += 1
        session.commit()

        clases_existentes = session.exec(select(ClaseHorario)).all()
        ya_existe = {
            (c.semestre_numero, c.dia, c.hora_inicio, c.materia) for c in clases_existentes
        }

        clases_insertadas = 0
        for semestre, dia, hora_inicio, hora_fin, materia, color, aula in CLASES:
            clave = (semestre, dia, hora_inicio, materia)
            if clave in ya_existe:
                continue
            session.add(ClaseHorario(
                semestre_numero=semestre,
                dia=dia,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                materia=materia,
                color=color,
                aula=aula,
            ))
            clases_insertadas += 1
        session.commit()

        print(f"Semestres insertados: {semestres_insertados}")
        print(f"Clases insertadas: {clases_insertadas} | Ya existían (saltadas): {len(CLASES) - clases_insertadas}")


if __name__ == "__main__":
    main()
