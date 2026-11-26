"""Conversión de fechas entre UTC (almacenamiento) y hora de Colombia (respuestas)."""

from datetime import datetime, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import PlainSerializer

COLOMBIA = ZoneInfo("America/Bogota")


def formato_colombia(fecha: datetime) -> str:
    """Devuelve `AAAA-MM-DD HH:MM:SS -05:00`. Una fecha sin zona se asume UTC."""
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(COLOMBIA).strftime("%Y-%m-%d %H:%M:%S -05:00")


def filtro_a_utc(fecha: datetime | None) -> datetime | None:
    """Normaliza `desde`/`hasta`. Sin zona horaria se interpreta como hora de Colombia."""
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=COLOMBIA)
    return fecha.astimezone(timezone.utc)


FechaColombia = Annotated[datetime, PlainSerializer(formato_colombia, return_type=str)]
