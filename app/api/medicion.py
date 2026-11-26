from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.sensor import DB, sensor_existente
from app.crud import medicion as crud
from app.models import Sensor
from app.schemas.medicion import MedicionRead
from app.schemas.tiempo import filtro_a_utc

router = APIRouter(tags=["mediciones"])

SensorDeRuta = Annotated[Sensor, Depends(sensor_existente)]


@router.get("/mediciones/{id}", response_model=MedicionRead)
def obtener_medicion(id: Annotated[int, Path(ge=1, le=9_223_372_036_854_775_807)], db: DB):
    medicion = crud.obtener(db, id)
    if medicion is None:
        raise HTTPException(404, f"No existe una medición con id {id}")
    return medicion


@router.get("/sensores/{id}/mediciones", response_model=list[MedicionRead])
def listar_mediciones(
    sensor: SensorDeRuta,
    db: DB,
    magnitud: Annotated[str | None, Query(max_length=50)] = None,
    desde: Annotated[datetime | None, Query(description="Sin zona = hora de Colombia")] = None,
    hasta: Annotated[datetime | None, Query(description="Sin zona = hora de Colombia")] = None,
    limit: Annotated[int | None, Query(ge=1, le=10_000, description="Últimas N mediciones")] = None,
):
    desde_utc, hasta_utc = filtro_a_utc(desde), filtro_a_utc(hasta)
    if desde_utc and hasta_utc and desde_utc > hasta_utc:
        raise HTTPException(400, "El parámetro 'desde' no puede ser posterior a 'hasta'")
    return crud.listar_por_sensor(db, sensor.id, magnitud, desde_utc, hasta_utc, limit)


@router.get("/sensores/{id}/ultima-medicion", response_model=MedicionRead)
def obtener_ultima_medicion(
    sensor: SensorDeRuta,
    db: DB,
    magnitud: Annotated[str | None, Query(max_length=50)] = None,
):
    mediciones = crud.listar_por_sensor(db, sensor.id, magnitud=magnitud, limit=1)
    if not mediciones:
        raise HTTPException(404, "El sensor no tiene mediciones para esa consulta")
    return mediciones[0]
