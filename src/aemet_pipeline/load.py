from __future__ import annotations

import json

from sqlalchemy import delete
from sqlalchemy.orm import Session

from aemet_pipeline.db import PrediccionDiaria, RawIngestion, now_iso
from aemet_pipeline.transform import PrediccionDiaria as PrediccionDiariaRow


def save_raw(session: Session, municipio_id: str, raw: list[dict]) -> None:
    session.add(
        RawIngestion(
            municipio_id=municipio_id,
            fetched_at=now_iso(),
            payload=json.dumps(raw, ensure_ascii=False),
        )
    )
    session.commit()


def upsert_predicciones(session: Session, filas: list[PrediccionDiariaRow]) -> int:
    """Inserta las predicciones del día, sustituyendo cualquier fila previa
    para la misma (municipio, fecha).

    AEMET actualiza la predicción de un mismo día varias veces al día, así
    que re-ejecutar el pipeline debe reflejar la última predicción conocida,
    no acumular filas duplicadas.
    """
    for fila in filas:
        session.execute(
            delete(PrediccionDiaria).where(
                PrediccionDiaria.municipio == fila["municipio"],
                PrediccionDiaria.fecha == fila["fecha"],
            )
        )
        session.add(
            PrediccionDiaria(
                municipio=fila["municipio"],
                provincia=fila["provincia"],
                fecha=fila["fecha"],
                temp_maxima=fila["temp_maxima"],
                temp_minima=fila["temp_minima"],
                prob_precipitacion=fila["prob_precipitacion"],
                estado_cielo=fila["estado_cielo"],
                inserted_at=fila["inserted_at"],
            )
        )

    session.commit()
    return len(filas)
