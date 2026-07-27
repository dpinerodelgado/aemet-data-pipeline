# aemet-data-pipeline

Pipeline ETL que descarga la predicción meteorológica diaria de [AEMET
OpenData](https://opendata.aemet.es/) (API pública y gratuita de la Agencia
Estatal de Meteorología), la normaliza y la almacena, con dos formas de
ejecución sobre **el mismo código**:

1. **Producción real**, desplegada en mi homelab (Docker + Postgres),
   corriendo cada 3 horas y alimentando un dashboard interno.
2. **Prueba pública**, en GitHub Actions: un workflow programado ejecuta el
   pipeline contra una base de datos efímera y publica un snapshot estático
   en GitHub Pages. Así cualquiera puede comprobar que el pipeline funciona
   de verdad, en vivo, sin depender de que mi mini PC esté encendido.

**Snapshot en vivo:** https://dpinerodelgado.github.io/aemet-data-pipeline/
(se actualiza solo cada 3 horas vía GitHub Actions).

## Por qué este proyecto

No es un ejercicio con un CSV estático: la fuente de datos cambia varias
veces al día de verdad, y la API tiene una particularidad real que hay que
manejar en el código (ver `src/aemet_pipeline/extract.py`):

- La llamada al endpoint de predicción **no devuelve los datos**, devuelve
  una URL temporal donde están; hay que hacer una segunda petición.
- Esa segunda respuesta viene codificada en **latin-1**, no en UTF-8 — si se
  decodifica mal, los acentos y la "ñ" salen corruptos.
- La capa gratuita tiene un **rate limit estricto**: la primera vez que
  lancé el workflow público de GitHub Actions falló con `429 Too Many
  Requests` porque acababa de probar la key en local pocos minutos antes.
  El cliente (`extract.py`) reintenta con backoff respetando `Retry-After`
  si el servidor lo manda.

## Arquitectura

```
                    ┌─────────────────────┐
                    │   AEMET OpenData     │
                    │  (API pública, REST) │
                    └──────────┬───────────┘
                               │
                    src/aemet_pipeline/
                    extract → transform → load
                               │
              ┌────────────────┴────────────────┐
              │                                  │
    ┌─────────▼──────────┐           ┌───────────▼────────────┐
    │  Homelab (Docker)   │           │   GitHub Actions        │
    │  Postgres persistente│          │   SQLite efímero        │
    │  Ofelia (cron)       │          │   cron programado        │
    │  Metabase (dashboard)│          │   → docs/ (GitHub Pages) │
    │  Heartbeat→UptimeKuma│          │                          │
    └──────────────────────┘          └──────────────────────────┘
        "producción real"                  "prueba pública"
```

El único cambio de comportamiento entre los dos entornos es la variable de
entorno `DATABASE_URL` (Postgres vs SQLite) — todo lo demás (extracción,
transformación, validación) es idéntico, lo que demuestra que el pipeline
es portable entre un entorno on-prem y uno efímero de CI.

## Estructura del repo

```
src/aemet_pipeline/
  extract.py        # cliente AEMET (llamada en dos pasos + encoding)
  transform.py       # funciones puras: JSON crudo → filas normalizadas
  db.py               # esquema SQLAlchemy (raw_ingestions + predicciones_diarias)
  load.py             # upsert idempotente (misma fecha = se sustituye, no se duplica)
  heartbeat.py        # notifica éxito/fallo a un monitor Push de Uptime Kuma
  run_pipeline.py     # entrypoint: extract → transform → load → heartbeat
tests/
  test_transform.py  # tests unitarios sobre una fixture real, sin red
scripts/
  publish_snapshot.py # genera docs/index.html a partir de la BD
docker-compose.yml    # despliegue de producción (homelab)
.github/workflows/
  ci.yml              # lint + tests en cada push
  scheduled-run.yml   # cron público + publicación en GitHub Pages
```

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows
pip install -e ".[dev]"
cp .env.example .env        # y rellena AEMET_API_KEY
ruff check .
pytest -v
python -m aemet_pipeline.run_pipeline   # usa SQLite por defecto (.env)
```

Consigue una API key gratuita en el [área de desarrolladores de
AEMET](https://opendata.aemet.es/centrodedescargas/altaUsuario).

## Despliegue en el homelab

```bash
docker network create homelab   # si no existe ya
cp .env.example .env             # rellenar AEMET_API_KEY, POSTGRES_PASSWORD, etc.
docker compose build pipeline
docker compose up -d postgres ofelia metabase
```

Ofelia lanza un contenedor nuevo de `aemet-pipeline` cada 3 horas
(`job-run`, ver labels en `docker-compose.yml`) y lo destruye al terminar —
no hay un contenedor de pipeline corriendo en segundo plano todo el rato.
Si `UPTIME_KUMA_PUSH_URL` está configurada, cada ejecución (éxito o fallo)
se refleja como un monitor más en Uptime Kuma, igual que el resto de
servicios del homelab.

> Nota: si despliegas pegando el YAML directamente en el editor web de
> Portainer en vez de con `docker compose` por SSH, recuerda que ese método
> no sube el `.env` — hay que sustituir los `${VAR}` por sus valores reales
> a mano en ese caso.

## CI/CD pública (GitHub Actions)

- `ci.yml`: lint (`ruff`) + tests (`pytest`) en cada push/PR. Es lo primero
  que mira un reclutador en la pestaña Actions.
- `scheduled-run.yml`: cada 3 horas ejecuta el pipeline completo contra un
  SQLite efímero y publica el resultado en `docs/index.html` (servido por
  GitHub Pages). Requiere un secreto de repo `AEMET_API_KEY`.

Para activarlo en tu propio fork/repo:
1. `Settings → Secrets and variables → Actions` → nuevo secreto
   `AEMET_API_KEY`.
2. `Settings → Pages` → Source: `Deploy from a branch`, branch `main`,
   carpeta `/docs`.
3. Lanza el workflow manualmente la primera vez (`workflow_dispatch`) para
   no esperar a la siguiente hora en punto.

## Decisiones de diseño (y alternativas descartadas)

- **Ofelia en vez de Airflow/Prefect**: para una sola fuente de datos,
  levantar un orquestador pesado en un mini PC de 16GB habría sido
  sobre-ingeniería — más una palabra de CV que una necesidad real. Ofelia
  es el mismo patrón "cron nativo de Docker" que ya uso para otras tareas
  del homelab.
- **Landing zone (`raw_ingestions`) además de la tabla limpia**: guardar el
  JSON crudo permite reprocesar el histórico si cambia la lógica de
  `transform.py`, sin depender de que AEMET siga sirviendo esas fechas
  concretas (su ventana de predicción es de solo 7 días).
- **Upsert por (municipio, fecha) en vez de solo insertar**: AEMET actualiza
  la predicción de un mismo día varias veces — re-ejecutar el pipeline debe
  reflejar la predicción más reciente, no acumular filas duplicadas.
- **SQLite efímero en CI, no un Postgres compartido con el homelab**: exponer
  el Postgres del homelab a internet para que GitHub Actions escriba en él
  sería abrir una superficie de ataque innecesaria. Cada entorno tiene su
  propia base; el punto de la ejecución pública es demostrar que el
  pipeline funciona, no compartir almacenamiento.
