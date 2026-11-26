from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class SensorMagnitud(Base):
    __tablename__ = "sensor_magnitudes"
    __table_args__ = (
        UniqueConstraint("sensor_id", "magnitud"),
        CheckConstraint("valor_minimo < valor_maximo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT")
    )
    magnitud: Mapped[str] = mapped_column(String(50))
    unidad: Mapped[str] = mapped_column(String(20))
    valor_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    valor_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 4))

    sensor: Mapped["Sensor"] = relationship(back_populates="magnitudes")
    mediciones: Mapped[list["Medicion"]] = relationship(
        back_populates="sensor_magnitud", passive_deletes="all"
    )
