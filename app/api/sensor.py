from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.crud import sensor as crud
from app.database.connection import get_db
from app.models import Sensor
from app.schemas.sensor import SensorRead

router = APIRouter(prefix="/sensores", tags=["sensores"])

DB = Annotated[Session, Depends(get_db)]
IdEntero = Annotated[int, Path(ge=1, le=2_147_483_647)]


def sensor_existente(id: IdEntero, db: DB) -> Sensor:
    """Dependencia compartida: devuelve el sensor o responde 404."""
    sensor = crud.obtener(db, id)
    if sensor is None:
        raise HTTPException(404, f"No existe un sensor con id {id}")
    return sensor


@router.get("", response_model=list[SensorRead])
def listar_sensores(db: DB):
    return crud.listar(db)


@router.get("/por-codigo/{codigo}", response_model=SensorRead)
def obtener_sensor_por_codigo(codigo: Annotated[str, Path(max_length=20)], db: DB):
    sensor = crud.obtener_por_codigo(db, codigo)
    if sensor is None:
        raise HTTPException(404, f"No existe un sensor con código {codigo}")
    return sensor


@router.get("/{id}", response_model=SensorRead)
def obtener_sensor(sensor: Annotated[Sensor, Depends(sensor_existente)]):
    return sensor
