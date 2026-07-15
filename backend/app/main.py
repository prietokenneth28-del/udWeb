"""
API REST del plan de estudios.

Endpoints (tal como se describen en el documento de arquitectura):
    GET  /api/plan-estudios     -> malla curricular completa (ciclos > semestres > materias)
    GET  /api/historial         -> materias cursadas y sus notas
    POST /api/historial         -> registra una nueva nota
    PUT  /api/historial/{id}    -> actualiza una nota existente
    GET  /api/estadisticas      -> créditos aprobados y PAPA

Ejecutar en desarrollo:
    uvicorn app.main:app --reload
Documentación interactiva (Swagger): http://localhost:8000/docs
"""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

app = FastAPI(
    title="API — Plan de Estudios Ingeniería Mecánica",
    description="Backend para el seguimiento de créditos, historial académico y PAPA.",
    version="1.0.0",
)

# Habilita que tu frontend (index.html servido desde otro origen/puerto,
# p. ej. Live Server en :5500) pueda llamar a esta API. En producción
# reemplaza "*" por el dominio real donde publiques el frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/plan-estudios", response_model=list[schemas.CicloOut])
def read_plan_estudios(db: Session = Depends(get_db)):
    """Devuelve toda la malla curricular: ciclos, semestres y materias."""
    return crud.get_plan_estudios(db)


@app.get("/api/historial", response_model=list[schemas.HistorialOut])
def read_historial(db: Session = Depends(get_db)):
    """Devuelve las materias cursadas y sus notas."""
    return crud.get_historial(db)


@app.post("/api/historial", response_model=schemas.HistorialOut, status_code=201)
def create_historial(data: schemas.HistorialCreate, db: Session = Depends(get_db)):
    """Registra una nueva nota al finalizar un semestre (o al inscribir una materia en curso)."""
    return crud.create_historial(db, data)


@app.put("/api/historial/{historial_id}", response_model=schemas.HistorialOut)
def update_historial(
    historial_id: int, data: schemas.HistorialUpdate, db: Session = Depends(get_db)
):
    """Actualiza la nota (o el periodo) de un registro de historial existente."""
    registro = crud.get_historial_by_id(db, historial_id)
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro de historial no encontrado")
    return crud.update_historial(db, registro, data)


@app.get("/api/estadisticas", response_model=schemas.EstadisticasOut)
def read_estadisticas(db: Session = Depends(get_db)):
    """Calcula créditos aprobados, % de avance y el promedio ponderado (PAPA)."""
    return crud.get_estadisticas(db)
