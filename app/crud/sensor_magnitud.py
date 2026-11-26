"""Consultas de magnitudes por sensor. El catálogo es de solo lectura."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SensorMagnitud


def listar_por_sensor(db: Session, sensor_id: int) -> list[SensorMagnitud]:
    consulta = select(SensorMagnitud).where(SensorMagnitud.sensor_id == sensor_id)
    return list(db.scalars(consulta.order_by(SensorMagnitud.id)))


def obtener(db: Session, sensor_magnitud_id: int) -> SensorMagnitud | None:
    return db.get(SensorMagnitud, sensor_magnitud_id)
