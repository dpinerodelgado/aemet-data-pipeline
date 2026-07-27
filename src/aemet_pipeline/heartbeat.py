"""Notifica el resultado de la ejecución a un monitor "Push" de Uptime Kuma.

Reutiliza la misma observabilidad que ya vigila el resto de servicios del
homelab: si el pipeline falla, salta como una alerta más, no como un script
silencioso que nadie mira.
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


def notify(push_url: str, ok: bool, message: str = "") -> None:
    if not push_url:
        logger.info("UPTIME_KUMA_PUSH_URL no configurada, se omite el heartbeat")
        return

    status = "up" if ok else "down"
    try:
        requests.get(push_url, params={"status": status, "msg": message}, timeout=10)
    except requests.RequestException:
        logger.warning("No se pudo notificar a Uptime Kuma", exc_info=True)
