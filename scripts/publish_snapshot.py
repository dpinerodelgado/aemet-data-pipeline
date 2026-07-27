"""Genera docs/index.html a partir de la base de datos poblada por el
pipeline, para publicarlo en GitHub Pages.

Esta es la "prueba pública" de que el pipeline funciona de verdad, sin
depender de que el mini PC del homelab esté encendido: GitHub Actions
ejecuta el pipeline contra una base efímera y este script vuelca el
resultado en una página estática con la hora de la última ejecución.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from sqlalchemy import select

from aemet_pipeline.config import Config
from aemet_pipeline.db import PrediccionDiaria, get_engine, get_session

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")


def _bar_chart_svg(filas: list[PrediccionDiaria]) -> str:
    width, height, padding = 640, 220, 30
    if not filas:
        return "<p>Sin datos todavía.</p>"

    temp_max_global = max(f.temp_maxima or 0 for f in filas)
    temp_min_global = min(f.temp_minima or 0 for f in filas)
    span = max(temp_max_global - temp_min_global, 1)
    plot_h = height - 2 * padding
    bar_w = (width - 2 * padding) / len(filas)

    bars = []
    for i, fila in enumerate(filas):
        x = padding + i * bar_w
        top_y = padding + plot_h * (1 - ((fila.temp_maxima or 0) - temp_min_global) / span)
        bot_y = padding + plot_h * (1 - ((fila.temp_minima or 0) - temp_min_global) / span)
        bars.append(
            f'<rect x="{x + bar_w * 0.2:.1f}" y="{top_y:.1f}" '
            f'width="{bar_w * 0.6:.1f}" height="{max(bot_y - top_y, 2):.1f}" '
            f'class="temp-bar" />'
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 8}" class="axis-label" '
            f'text-anchor="middle">{fila.fecha[5:]}</text>'
            f'<text x="{x + bar_w / 2:.1f}" y="{top_y - 6:.1f}" class="value-label" '
            f'text-anchor="middle">{fila.temp_maxima:.0f}°</text>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Temperaturas máximas y mínimas previstas">{"".join(bars)}</svg>'
    )


def _table_rows(filas: list[PrediccionDiaria]) -> str:
    rows = []
    for fila in filas:
        rows.append(
            "<tr>"
            f"<td>{fila.fecha}</td>"
            f"<td>{fila.temp_minima:.0f}°C – {fila.temp_maxima:.0f}°C</td>"
            f"<td>{fila.prob_precipitacion if fila.prob_precipitacion is not None else '—'}%</td>"
            f"<td>{fila.estado_cielo or '—'}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_html(filas: list[PrediccionDiaria], municipio: str) -> str:
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>aemet-data-pipeline — snapshot público</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.4rem; }}
  .meta {{ color: gray; font-size: 0.9rem; margin-bottom: 1.5rem; }}
  .temp-bar {{ fill: #4f8ef7; }}
  .axis-label, .value-label {{ font-size: 11px; fill: currentColor; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
  th, td {{ text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #8884; }}
</style>
</head>
<body>
  <h1>Predicción meteorológica — {municipio}</h1>
  <p class="meta">
    Generado automáticamente por GitHub Actions en cada ejecución programada.
    Última ejecución: {generated_at}. Este snapshot corre de forma independiente
    del homelab: prueba que el pipeline funciona sin depender de que el
    servidor de casa esté encendido.
  </p>
  {_bar_chart_svg(filas)}
  <table>
    <thead><tr><th>Fecha</th><th>Temperatura</th><th>Prob. lluvia</th><th>Cielo</th></tr></thead>
    <tbody>{_table_rows(filas)}</tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    config = Config()
    engine = get_engine(config.DATABASE_URL)

    with get_session(engine) as session:
        filas = list(
            session.scalars(
                select(PrediccionDiaria).order_by(PrediccionDiaria.fecha)
            )
        )

    municipio = filas[0].municipio if filas else config.AEMET_MUNICIPIO_ID
    html = build_html(filas, municipio)

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


if __name__ == "__main__":
    main()
