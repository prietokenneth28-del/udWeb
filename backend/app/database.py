"""
Configuración de la conexión a PostgreSQL.

La URL de conexión se lee de la variable de entorno DATABASE_URL
(definida en tu archivo .env). Formato esperado:

    postgresql+psycopg2://usuario:password@localhost:5432/plan_estudios
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/plan_estudios",
)

engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos."""
    pass


def get_db():
    """
    Dependencia de FastAPI: entrega una sesión de base de datos y
    garantiza que se cierre al terminar la petición, incluso si hubo
    un error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
