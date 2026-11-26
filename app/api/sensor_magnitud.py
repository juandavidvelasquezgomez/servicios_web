from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.sensor import DB, IdEntero, sensor_existente
from app.crud import sensor_magnitud as crud
from app.models import Sensor
from app.schemas.sensor_magnitud import SensorMagnitudRead

router = APIRouter(tags=["magnitudes"])


@router.get("/sensores/{id}/magnitudes", response_model=list[SensorMagnitudRead])
def listar_magnitudes_de_sensor(sensor: Annotated[Sensor, Depends(sensor_existente)], db: DB):
    return crud.listar_por_sensor(db, sensor.id)


@router.get("/sensor-magnitudes/{id}", response_model=SensorMagnitudRead)
def obtener_sensor_magnitud(id: IdEntero, db: DB):
    sensor_magnitud = crud.obtener(db, id)
    if sensor_magnitud is None:
        raise HTTPException(404, f"No existe una magnitud de sensor con id {id}")
    return sensor_magnitud
