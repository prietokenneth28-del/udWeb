from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import List, Optional
import json


class CicloAcademico(SQLModel, table=True):
    __tablename__ = "ciclo_academico"

    id: str = Field(primary_key=True)
    nombre: str


class Semestre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    numero: int
    ciclo_id: str = Field(foreign_key="ciclo_academico.id")


class Materia(SQLModel, table=True):
    id: str = Field(primary_key=True)
    nombre: str
    codigo: str
    creditos: float
    tipo: str
    categoria: str
    semestre_id: int = Field(foreign_key="semestre.id")
    prereq_json: str = "[]"

    @property
    def prereq(self) -> List[str]:
        return json.loads(self.prereq_json)

    @prereq.setter
    def prereq(self, value: List[str]):
        self.prereq_json = json.dumps(value)


class HistorialAcademico(SQLModel, table=True):
    __tablename__ = "historial_academico"

    id: Optional[int] = Field(default=None, primary_key=True)
    materia_id: str = Field(foreign_key="materia.id")
    periodo: Optional[str] = None
    nota_final: Optional[float] = None
    estado: str  # "Aprobada", "Reprobada", "En curso"
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str


class UserCreate(SQLModel):
    username: str
    password: str
