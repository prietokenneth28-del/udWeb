"""
Esquemas Pydantic (request/response). Separados de los modelos
SQLAlchemy a propósito: los modelos describen la tabla, estos
describen lo que la API recibe y devuelve.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# --- Materias / plan de estudios ----------------------------------------

class MateriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    codigo: Optional[str] = None
    creditos: int
    tipo: str
    categoria: Optional[str] = None
    semestre_id: int


class SemestreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    ciclo_id: int
    materias: list[MateriaOut] = []


class CicloOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    semestres: list[SemestreOut] = []


# --- Historial académico (notas) ----------------------------------------

class HistorialCreate(BaseModel):
    materia_id: int
    periodo: str = Field(..., examples=["2026-2"])
    nota_final: Optional[float] = Field(
        default=None, ge=0, le=5, description="Nota entre 0.0 y 5.0. Vacío = En curso."
    )


class HistorialUpdate(BaseModel):
    periodo: Optional[str] = None
    nota_final: Optional[float] = Field(default=None, ge=0, le=5)


class HistorialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    materia_id: int
    periodo: str
    nota_final: Optional[float] = None
    estado: str
    fecha_registro: datetime
    materia: Optional[MateriaOut] = None


# --- Estadísticas ---------------------------------------------------------

class DesgloseCiclo(BaseModel):
    creditos_totales: float
    creditos_aprobados: float


class EstadisticasOut(BaseModel):
    creditos_totales: float
    creditos_aprobados: float
    creditos_pendientes: float
    porcentaje_avance: float
    papa: Optional[float] = Field(
        default=None, description="Promedio aritmético ponderado acumulado (0.0-5.0)"
    )
    materias_cursadas: int
    desglose_por_ciclo: dict[str, DesgloseCiclo]
