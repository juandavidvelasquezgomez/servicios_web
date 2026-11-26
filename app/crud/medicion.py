"""Escritura y consulta de mediciones."""

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, contains_eager

from app.models import Medicion, SensorMagnitud


def _consulta_base() -> Select:
    return (
        select(Medicion)
        .join(Medicion.sensor_magnitud)
        .options(contains_eager(Medicion.sensor_magnitud))
    )


def crear_lote(db: Session, mediciones: list[Medicion]) -> list[Medicion]:
    """Guarda todas las mediciones de un payload en una sola transacción."""
    try:
        db.add_all(mediciones)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return mediciones


def obtener(db: Session, medicion_id: int) -> Medicion | None:
    return db.scalar(_consulta_base().where(Medicion.id == medicion_id))


def listar_por_sensor(
    db: Session,
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = None,
) -> list[Medicion]:
    """Histórico de un sensor, de la más reciente a la más antigua. Los filtros se combinan."""
    consulta = _consulta_base().where(SensorMagnitud.sensor_id == sensor_id)
    if magnitud is not None:
        consulta = consulta.where(SensorMagnitud.magnitud == magnitud)
    if desde is not None:
        consulta = consulta.where(Medicion.timestamp_utc >= desde)
    if hasta is not None:
        consulta = consulta.where(Medicion.timestamp_utc <= hasta)
    consulta = consulta.order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc())
    if limit is not None:
        consulta = consulta.limit(limit)
    return list(db.scalars(consulta))
