import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    AEMET_API_KEY = os.environ.get("AEMET_API_KEY", "")
    AEMET_MUNICIPIO_ID = os.environ.get("AEMET_MUNICIPIO_ID", "28079")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///aemet.db")
    UPTIME_KUMA_PUSH_URL = os.environ.get("UPTIME_KUMA_PUSH_URL", "")
