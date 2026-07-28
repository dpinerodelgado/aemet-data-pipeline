"""Tests E2E sobre el snapshot público (GitHub Pages) del pipeline de AEMET."""

URL = "https://dpinerodelgado.github.io/aemet-data-pipeline/"


def test_homepage_carga(page):
    page.goto(URL)

    # TODO 1: comprueba que el título de la página (page.title()) contiene
    #         algo esperado. Pista: mira el <title> de la web con las
    #         herramientas de desarrollador del navegador (F12), o pregúntame.
    assert "snapshot público" in page.title()

    # TODO 2: comprueba que el encabezado principal (h1) es visible en
    #         pantalla. Pista: page.locator("h1") te da el elemento;
    #         .is_visible() o el assert de Playwright expect(...).to_be_visible()
    #         te dicen si aparece.
    assert page.locator("h1").is_visible()

    # TODO 3: comprueba que la tabla de predicción tiene contenido (por
    #         ejemplo, que existe al menos una fila <tr> dentro de <tbody>).
    filas = page.locator("tbody tr").count()
    assert filas > 0
