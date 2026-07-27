"""Transformación de la respuesta cruda de AEMET a filas planas y tipadas.

Funciones puras (sin red, sin base de datos) para que sean fáciles de
testear: dado un JSON de ejemplo, siempre producen el mismo resultado.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict


class PrediccionDiaria(TypedDict):
    municipio: str
    provincia: str
    fecha: str  # ISO date (YYYY-MM-DD)
    temp_maxima: float | None
    temp_minima: float | None
    prob_precipitacion: int | None
    estado_cielo: str | None
    inserted_at: str


def _primer_valor(lista: list[dict] | None, clave: str) -> Any:
    """Los campos de AEMET (probPrecipitacion, estadoCielo...) vienen como
    una lista de periodos horarios; para un resumen diario simple tomamos
    el primer periodo disponible (normalmente "00-24", el del día completo).
    """
    if not lista:
        return None
    return lista[0].get(clave)


def parse_prediccion_municipio(raw: list[dict]) -> list[PrediccionDiaria]:
    """Convierte la respuesta cruda de fetch_prediccion_diaria() en filas planas."""
    if not raw:
        return []

    municipio_data = raw[0]
    municipio = municipio_data.get("nombre", "desconocido")
    provincia = municipio_data.get("provincia", "desconocida")
    dias = municipio_data.get("prediccion", {}).get("dia", [])

    now = datetime.now(UTC).isoformat()
    filas: list[PrediccionDiaria] = []

    for dia in dias:
        fecha_raw = dia.get("fecha", "")
        fecha = fecha_raw.split("T")[0] if fecha_raw else ""

        temperatura = dia.get("temperatura", {})

        filas.append(
            PrediccionDiaria(
                municipio=municipio,
                provincia=provincia,
                fecha=fecha,
                temp_maxima=temperatura.get("maxima"),
                temp_minima=temperatura.get("minima"),
                prob_precipitacion=_primer_valor(dia.get("probPrecipitacion"), "value"),
                estado_cielo=_primer_valor(dia.get("estadoCielo"), "descripcion"),
                inserted_at=now,
            )
        )

    return filas
