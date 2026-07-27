from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class RawIngestion(Base):
    """Landing zone: guarda la respuesta cruda de AEMET tal cual llega.

    Permite reprocesar datos históricos si cambia la lógica de transform.py
    sin depender de que la API siga sirviendo esas fechas.
    """

    __tablename__ = "raw_ingestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    municipio_id: Mapped[str] = mapped_column(String(10))
    fetched_at: Mapped[str] = mapped_column(String(40))
    payload: Mapped[str] = mapped_column(Text)


class PrediccionDiaria(Base):
    __tablename__ = "predicciones_diarias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    municipio: Mapped[str] = mapped_column(String(120))
    provincia: Mapped[str] = mapped_column(String(120))
    fecha: Mapped[str] = mapped_column(String(10))
    temp_maxima: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_minima: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_precipitacion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado_cielo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inserted_at: Mapped[str] = mapped_column(String(40))


def get_engine(database_url: str):
    return create_engine(database_url, future=True)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def get_session(engine) -> Session:
    return Session(engine)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
