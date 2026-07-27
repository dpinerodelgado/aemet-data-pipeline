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
"""

from __future__ import annotations

import json

import requests

BASE_URL = "https://opendata.aemet.es/opendata/api"
REQUEST_TIMEOUT = 15


class AemetError(RuntimeError):
    pass


def _decode_latin1_json(response: requests.Response):
    return json.loads(response.content.decode("latin-1"))


def fetch_prediccion_diaria(municipio_id: str, api_key: str) -> list[dict]:
    """Descarga la predicción diaria (7 días) de un municipio.

    Devuelve la estructura tal cual la sirve AEMET: una lista con un único
    elemento (el municipio), con la predicción diaria en ["prediccion"]["dia"].
    """
    if not api_key:
        raise AemetError("Falta AEMET_API_KEY (regístrate en opendata.aemet.es)")

    envelope_url = f"{BASE_URL}/prediccion/especifica/municipio/diaria/{municipio_id}"
    envelope_response = requests.get(
        envelope_url, params={"api_key": api_key}, timeout=REQUEST_TIMEOUT
    )
    envelope_response.raise_for_status()
    envelope = envelope_response.json()

    if envelope.get("estado") != 200:
        raise AemetError(f"AEMET respondió {envelope.get('estado')}: {envelope.get('descripcion')}")

    datos_response = requests.get(envelope["datos"], timeout=REQUEST_TIMEOUT)
    datos_response.raise_for_status()
    return _decode_latin1_json(datos_response)
