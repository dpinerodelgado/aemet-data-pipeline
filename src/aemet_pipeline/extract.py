"""Cliente de la API de AEMET OpenData.

La API funciona en dos pasos, particularidad habitual de este tipo de APIs
públicas que conviene conocer:

1. Se llama al endpoint "de verdad" (ej. predicción diaria de un municipio)
   y NO devuelve los datos, sino un JSON pequeño con una URL temporal en el
   campo "datos".
2. Esa URL temporal es la que hay que descargar para obtener el JSON real
   con la predicción.

Además, el JSON del segundo paso viene codificado en latin-1 (ISO-8859-15)
en vez de UTF-8: si se decodifica como UTF-8 sin más, los acentos y la "ñ"
de campos como "estadoCielo" o nombres de provincia salen corruptos.

Por último, la capa gratuita de AEMET tiene un límite de peticiones bastante
estricto (se observó un 429 al llamar dos veces en pocos minutos): el
cliente reintenta automáticamente respetando "Retry-After" si el servidor
lo manda, o con backoff progresivo si no.
"""

from __future__ import annotations

import json
import logging
import time

import requests

BASE_URL = "https://opendata.aemet.es/opendata/api"
REQUEST_TIMEOUT = 15
MAX_ATTEMPTS = 4
DEFAULT_BACKOFF_SECONDS = 30

logger = logging.getLogger(__name__)


class AemetError(RuntimeError):
    pass


def _decode_latin1_json(response: requests.Response):
    return json.loads(response.content.decode("latin-1"))


def _get_with_retry(url: str, params: dict | None = None) -> requests.Response:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

        if response.status_code != 429:
            response.raise_for_status()
            return response

        if attempt == MAX_ATTEMPTS:
            response.raise_for_status()

        wait_seconds = int(response.headers.get("Retry-After", DEFAULT_BACKOFF_SECONDS * attempt))
        logger.warning(
            "AEMET devolvió 429 (intento %d/%d), esperando %ds antes de reintentar",
            attempt,
            MAX_ATTEMPTS,
            wait_seconds,
        )
        time.sleep(wait_seconds)

    raise AemetError("Se agotaron los reintentos frente a los 429 de AEMET")


def fetch_prediccion_diaria(municipio_id: str, api_key: str) -> list[dict]:
    """Descarga la predicción diaria (7 días) de un municipio.

    Devuelve la estructura tal cual la sirve AEMET: una lista con un único
    elemento (el municipio), con la predicción diaria en ["prediccion"]["dia"].
    """
    if not api_key:
        raise AemetError("Falta AEMET_API_KEY (regístrate en opendata.aemet.es)")

    envelope_url = f"{BASE_URL}/prediccion/especifica/municipio/diaria/{municipio_id}"
    envelope_response = _get_with_retry(envelope_url, params={"api_key": api_key})
    envelope = envelope_response.json()

    if envelope.get("estado") != 200:
        raise AemetError(f"AEMET respondió {envelope.get('estado')}: {envelope.get('descripcion')}")

    datos_response = _get_with_retry(envelope["datos"])
    return _decode_latin1_json(datos_response)
