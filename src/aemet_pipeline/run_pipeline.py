"""Entrypoint del pipeline: extract -> transform -> load -> heartbeat.

Funciona igual en el homelab (Postgres, disparado por Ofelia) que en
GitHub Actions (SQLite efímero, disparado por un cron de la propia
Action): el único cambio entre ambos entornos es la variable de entorno
DATABASE_URL.
"""

from __future__ import annotations

import logging
import sys

from aemet_pipeline.config import Config
from aemet_pipeline.db import get_engine, get_session, init_db
from aemet_pipeline.extract import AemetError, fetch_prediccion_diaria
from aemet_pipeline.heartbeat import notify
from aemet_pipeline.load import save_raw, upsert_predicciones
from aemet_pipeline.transform import parse_prediccion_municipio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run() -> int:
    config = Config()
    engine = get_engine(config.DATABASE_URL)
    init_db(engine)

    try:
        raw = fetch_prediccion_diaria(config.AEMET_MUNICIPIO_ID, config.AEMET_API_KEY)
        filas = parse_prediccion_municipio(raw)

        with get_session(engine) as session:
            save_raw(session, config.AEMET_MUNICIPIO_ID, raw)
            total = upsert_predicciones(session, filas)

        logger.info("Pipeline OK: %d filas cargadas para municipio %s", total, config.AEMET_MUNICIPIO_ID)
        notify(config.UPTIME_KUMA_PUSH_URL, ok=True, message=f"{total} filas cargadas")
        return 0

    except AemetError as exc:
        logger.error("Fallo de la API de AEMET: %s", exc)
        notify(config.UPTIME_KUMA_PUSH_URL, ok=False, message=str(exc))
        return 1
    except Exception as exc:
        logger.exception("Fallo inesperado en el pipeline")
        notify(config.UPTIME_KUMA_PUSH_URL, ok=False, message=str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(run())
