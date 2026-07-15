"""
Puebla Ciclos_Academicos, Semestres y Materias con la malla curricular
real (extraída de tu index.html / courses-data.js), a partir de
data/materias_seed.json.

OJO: este script NO toca Historial_Academico — las notas las vas
ingresando tú a medida que cursas, vía POST /api/historial (o desde el
Swagger UI en /docs). No inventamos notas de materias que ya marcaste
como aprobadas en el frontend, porque esas notas reales no estaban en
ningún lado; tendrás que capturarlas una vez, a mano.

Ejecutar (con el entorno virtual activado y la base de datos ya
migrada con Alembic):
    python -m app.seed
"""
import json
from pathlib import Path

from app.database import SessionLocal, engine, Base
from app import models

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "materias_seed.json"


def run():
    Base.metadata.create_all(bind=engine)  # no-op si ya migraste con Alembic

    with open(SEED_FILE, encoding="utf-8") as f:
        materias_seed = json.load(f)

    db = SessionLocal()
    try:
        if db.query(models.Materia).count() > 0:
            print("La tabla Materias ya tiene datos — no se vuelve a sembrar.")
            print("Si quieres resembrar, vacía las tablas primero.")
            return

        ciclos_cache: dict[str, models.CicloAcademico] = {}
        semestres_cache: dict[tuple[str, int], models.Semestre] = {}

        for item in materias_seed:
            nombre_ciclo = item["ciclo"]
            if nombre_ciclo not in ciclos_cache:
                ciclo = models.CicloAcademico(nombre=nombre_ciclo)
                db.add(ciclo)
                db.flush()  # asigna el id sin cerrar la transacción
                ciclos_cache[nombre_ciclo] = ciclo

            key = (nombre_ciclo, item["semestre"])
            if key not in semestres_cache:
                semestre = models.Semestre(
                    numero=item["semestre"], ciclo_id=ciclos_cache[nombre_ciclo].id
                )
                db.add(semestre)
                db.flush()
                semestres_cache[key] = semestre

            materia = models.Materia(
                nombre=item["nombre"],
                codigo=item["codigo"],
                creditos=int(item["creditos"]),
                tipo=item["tipo"],
                categoria=item["categoria"],
                semestre_id=semestres_cache[key].id,
            )
            db.add(materia)

        db.commit()
        print(f"Sembradas {len(materias_seed)} materias en "
              f"{len(semestres_cache)} semestres y {len(ciclos_cache)} ciclos.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
