"""Pruebas con una base SQLite en memoria: no tocan la base ni el broker del curso."""

import os
from decimal import Decimal

os.environ["MQTT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.main import app
from app.models import Sensor, SensorMagnitud


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    event.listen(engine, "connect", lambda con, _: con.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as sesion:
        gas = Sensor(codigo="GAS-002", nombre="Gas de prueba", categoria="GAS", ubicacion="Lab")
        gas.magnitudes = [
            SensorMagnitud(magnitud=n, unidad=u, valor_minimo=Decimal(a), valor_maximo=Decimal(b))
            for n, u, a, b in (
                ("ch4", "ppm", 0, 10000),
                ("temperature", "C", -10, 60),
                ("humidity", "%", 0, 100),
            )
        ]
        inactivo = Sensor(
            codigo="OFF-001", nombre="Inactivo", categoria="AIRE", ubicacion="Lab", activo=False
        )
        sesion.add_all([gas, inactivo])
        sesion.commit()
        yield sesion
    engine.dispose()


@pytest.fixture
def api(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
