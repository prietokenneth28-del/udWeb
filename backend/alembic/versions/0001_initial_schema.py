"""esquema inicial: ciclos, semestres, materias, historial

Revision ID: 0001
Revises:
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ciclos_academicos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False, unique=True),
    )

    op.create_table(
        "semestres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column(
            "ciclo_id",
            sa.Integer(),
            sa.ForeignKey("ciclos_academicos.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.create_table(
        "materias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("creditos", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=True),
        sa.Column("categoria", sa.String(length=50), nullable=True),
        sa.Column(
            "semestre_id",
            sa.Integer(),
            sa.ForeignKey("semestres.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.create_table(
        "historial_academico",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "materia_id",
            sa.Integer(),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("periodo", sa.String(length=20), nullable=False),
        sa.Column("nota_final", sa.Numeric(3, 1), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="En curso"),
        sa.Column(
            "fecha_registro",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("historial_academico")
    op.drop_table("materias")
    op.drop_table("semestres")
    op.drop_table("ciclos_academicos")
