"""Fixture con la forma real de la respuesta de AEMET para
prediccion/especifica/municipio/diaria (recortada a 2 días para el test).
"""

PREDICCION_MADRID = [
    {
        "origen": {
            "productor": "Agencia Estatal de Meteorología - AEMET. Gobierno de España",
            "web": "https://www.aemet.es",
        },
        "elaborado": "2026-07-27T09:00:00",
        "nombre": "Madrid",
        "provincia": "Madrid",
        "prediccion": {
            "dia": [
                {
                    "fecha": "2026-07-27T00:00:00",
                    "probPrecipitacion": [{"value": 5, "periodo": "00-24"}],
                    "estadoCielo": [
                        {"value": "11", "descripcion": "Despejado", "periodo": "00-24"}
                    ],
                    "viento": [{"direccion": "NE", "velocidad": 10, "periodo": "00-24"}],
                    "temperatura": {"maxima": 36, "minima": 21},
                    "sensTermica": {"maxima": 38, "minima": 21},
                    "humedadRelativa": {"maxima": 40, "minima": 15},
                },
                {
                    "fecha": "2026-07-28T00:00:00",
                    "probPrecipitacion": [{"value": 20, "periodo": "00-24"}],
                    "estadoCielo": [
                        {"value": "13", "descripcion": "Nuboso", "periodo": "00-24"}
                    ],
                    "viento": [{"direccion": "SO", "velocidad": 15, "periodo": "00-24"}],
                    "temperatura": {"maxima": 30, "minima": 18},
                    "sensTermica": {"maxima": 30, "minima": 18},
                    "humedadRelativa": {"maxima": 55, "minima": 20},
                },
            ]
        },
    }
]
