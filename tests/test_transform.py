from fixtures_prediccion_madrid import PREDICCION_MADRID

from aemet_pipeline.transform import parse_prediccion_municipio


def test_parse_prediccion_devuelve_una_fila_por_dia():
    filas = parse_prediccion_municipio(PREDICCION_MADRID)
    assert len(filas) == 2


def test_parse_prediccion_extrae_municipio_y_provincia():
    filas = parse_prediccion_municipio(PREDICCION_MADRID)
    assert filas[0]["municipio"] == "Madrid"
    assert filas[0]["provincia"] == "Madrid"


def test_parse_prediccion_normaliza_fecha_a_solo_dia():
    filas = parse_prediccion_municipio(PREDICCION_MADRID)
    assert filas[0]["fecha"] == "2026-07-27"
    assert filas[1]["fecha"] == "2026-07-28"


def test_parse_prediccion_extrae_temperaturas():
    filas = parse_prediccion_municipio(PREDICCION_MADRID)
    assert filas[0]["temp_maxima"] == 36
    assert filas[0]["temp_minima"] == 21


def test_parse_prediccion_toma_el_primer_periodo_de_precipitacion_y_cielo():
    filas = parse_prediccion_municipio(PREDICCION_MADRID)
    assert filas[0]["prob_precipitacion"] == 5
    assert filas[0]["estado_cielo"] == "Despejado"


def test_parse_prediccion_con_lista_vacia_no_falla():
    assert parse_prediccion_municipio([]) == []


def test_parse_prediccion_con_dia_sin_precipitacion_devuelve_none():
    raw = [
        {
            "nombre": "Madrid",
            "provincia": "Madrid",
            "prediccion": {
                "dia": [
                    {
                        "fecha": "2026-07-27T00:00:00",
                        "temperatura": {"maxima": 30, "minima": 18},
                    }
                ]
            },
        }
    ]
    filas = parse_prediccion_municipio(raw)
    assert filas[0]["prob_precipitacion"] is None
    assert filas[0]["estado_cielo"] is None
