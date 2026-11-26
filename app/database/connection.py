"""Conexión con PostgreSQL.

Ejecutar `python -m app.database.connection` para verificar la conexión.
La aplicación no crea ni altera tablas: el esquema y el catálogo los entrega el docente.
"""

import os
from collections.abc import Iterator
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import URL, Engine, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def construir_url() -> URL:
    """Arma la URL a partir de variables de entorno (admite símbolos en la contraseña)."""
    faltantes = [v for v in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD") if not os.getenv(v)]
    if faltantes:
        raise RuntimeError(f"Faltan variables de entorno: {', '.join(faltantes)}")
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT") or 5432),
        database=os.environ["DB_NAME"],
    )


@lru_cache
def get_engine() -> Engine:
    return create_engine(construir_url(), pool_pre_ping=True, connect_args={"connect_timeout": 10})


def nueva_sesion() -> Session:
    return Session(get_engine())


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por solicitud."""
    with nueva_sesion() as db:
        yield db


def verificar_conexion() -> None:
    from app.models import Medicion, Sensor, SensorMagnitud

    with nueva_sesion() as db:
        for modelo in (Sensor, SensorMagnitud, Medicion):
            total = db.scalar(select(func.count()).select_from(modelo))
            print(f"{modelo.__tablename__}: {total} registros")
    print("Conexión con PostgreSQL correcta.")


if __name__ == "__main__":
    load_dotenv()
    verificar_conexion()
