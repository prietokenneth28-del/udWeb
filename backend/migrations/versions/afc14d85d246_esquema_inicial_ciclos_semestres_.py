"""esquema inicial ciclos semestres materias historial

Revision ID: afc14d85d246
Revises: 
Create Date: 2026-07-19 11:25:55.222950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afc14d85d246'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("course")

    op.create_table(
        "ciclo_academico",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("nombre", sa.String(), nullable=False),
    )

    op.create_table(
        "semestre",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("ciclo_id", sa.String(), sa.ForeignKey("ciclo_academico.id"), nullable=False),
    )

    op.create_table(
        "materia",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("codigo", sa.String(), nullable=False),
        sa.Column("creditos", sa.Float(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("categoria", sa.String(), nullable=False),
        sa.Column("semestre_id", sa.Integer(), sa.ForeignKey("semestre.id"), nullable=False),
        sa.Column("prereq_json", sa.String(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "historial_academico",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("materia_id", sa.String(), sa.ForeignKey("materia.id"), nullable=False),
        sa.Column("periodo", sa.String(), nullable=True),
        sa.Column("nota_final", sa.Float(), nullable=True),
        sa.Column("estado", sa.String(), nullable=False),
        sa.Column("fecha_registro", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("historial_academico")
    op.drop_table("materia")
    op.drop_table("semestre")
    op.drop_table("ciclo_academico")

    op.create_table(
        "course",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False),
        sa.Column("cycle", sa.String(), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("prereq_json", sa.String(), nullable=False, server_default="[]"),
    )
