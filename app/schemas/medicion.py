"""Schemas del payload MQTT (entrada) y de las mediciones consultadas (salida)."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.tiempo import FechaColombia

# ISO 8601 en UTC: 2026-10-07T16:25:30Z (admite fracciones de segundo y +00:00).
PATRON_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|\+00:00)")


class MedidaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    value: float = Field(allow_inf_nan=False)  # en modo estricto rechaza texto, booleanos y null
    unit: str = Field(min_length=1, max_length=20)


class MensajePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    sensor_id: str = Field(min_length=1, max_length=20)
    timestamp: datetime
    measurements: dict[str, MedidaPayload] = Field(min_length=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validar_timestamp(cls, valor: object) -> datetime:
        if not isinstance(valor, str) or not PATRON_UTC.fullmatch(valor):
            raise ValueError("se espera texto ISO 8601 en UTC, por ejemplo 2026-10-07T16:25:30Z")
        # fromisoformat rechaza fechas imposibles (mes 13, 30 de febrero, hora 25...).
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))


class MedicionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    sensor_magnitud_id: int
    magnitud: str
    unidad: str
    valor: float
    timestamp_utc: FechaColombia = Field(serialization_alias="fecha_hora_colombia")
    fecha_recepcion: FechaColombia
