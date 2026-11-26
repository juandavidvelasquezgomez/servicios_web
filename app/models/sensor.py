from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Sensor(Base):
    __tablename__ = "sensores"
    __table_args__ = (CheckConstraint("categoria IN ('AIRE', 'GAS', 'AGUA', 'AMBIENTE')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))
    categoria: Mapped[str] = mapped_column(String(30))
    ubicacion: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(server_default=true())
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    magnitudes: Mapped[list["SensorMagnitud"]] = relationship(back_populates="sensor", passive_deletes="all")
