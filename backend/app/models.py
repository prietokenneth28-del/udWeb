"""
Modelos SQLAlchemy — mapean 1 a 1 con las tablas descritas en
"Estructura_Backend_y_Base_de_Datos - Notas Académicas.pdf".

Nota: a la tabla Materias le agregué dos columnas que NO estaban en el
documento original — `codigo` y `categoria` — porque tu frontend
(courses-data.js) ya las usa para mostrar el código de cada materia y
el color por área (Física/Matemática, Fabricación, etc.). Sin ellas
perderías esa información al migrar del frontend al backend. Son
opcionales (nullable) y no rompen nada de lo que pide el documento.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    TIMESTAMP,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CicloAcademico(Base):
    __tablename__ = "ciclos_academicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    semestres: Mapped[list["Semestre"]] = relationship(
        back_populates="ciclo", cascade="all, delete-orphan"
    )


class Semestre(Base):
    __tablename__ = "semestres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    ciclo_id: Mapped[int] = mapped_column(
        ForeignKey("ciclos_academicos.id", ondelete="CASCADE"), nullable=False
    )

    ciclo: Mapped["CicloAcademico"] = relationship(back_populates="semestres")
    materias: Mapped[list["Materia"]] = relationship(
        back_populates="semestre", cascade="all, delete-orphan"
    )


class Materia(Base):
    __tablename__ = "materias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    creditos: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    # Columnas adicionales (ver nota en el docstring del módulo)
    codigo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(50), nullable=True)

    semestre_id: Mapped[int] = mapped_column(
        ForeignKey("semestres.id", ondelete="CASCADE"), nullable=False
    )

    semestre: Mapped["Semestre"] = relationship(back_populates="materias")
    historial: Mapped[list["HistorialAcademico"]] = relationship(
        back_populates="materia", cascade="all, delete-orphan"
    )


class HistorialAcademico(Base):
    __tablename__ = "historial_academico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    materia_id: Mapped[int] = mapped_column(
        ForeignKey("materias.id", ondelete="CASCADE"), nullable=False
    )
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    nota_final: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="En curso")
    fecha_registro: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    materia: Mapped["Materia"] = relationship(back_populates="historial")
