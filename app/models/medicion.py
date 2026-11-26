from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Medicion(Base):
    __tablename__ = "mediciones"
    __table_args__ = (
        Index("idx_mediciones_sensor_magnitud", "sensor_magnitud_id"),
        Index("idx_mediciones_timestamp_utc", "timestamp_utc"),
        Index("idx_mediciones_magnitud_timestamp", "sensor_magnitud_id", "timestamp_utc"),
    )

    # BIGSERIAL en PostgreSQL; la variante Integer solo se usa en las pruebas con SQLite.
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    sensor_magnitud_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT")
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_recepcion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sensor_magnitud: Mapped["SensorMagnitud"] = relationship(back_populates="mediciones")

    @property
    def sensor_id(self) -> int:
        return self.sensor_magnitud.sensor_id

    @property
    def magnitud(self) -> str:
        return self.sensor_magnitud.magnitud

    @property
    def unidad(self) -> str:
        return self.sensor_magnitud.unidad
