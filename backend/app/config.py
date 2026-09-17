"""
Configuración de la aplicación.

Todos los valores tienen un default seguro para desarrollo local, pero en
producción DEBEN sobreescribirse vía variables de entorno (ver .env.example).
Esto respalda la arquitectura de seguridad descrita en la sección J del
blueprint: nada sensible vive hardcodeado en el código.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # En desarrollo/test usamos SQLite por portabilidad. En producción,
    # DATABASE_URL debe apuntar a PostgreSQL (ver sección H del blueprint).
    database_url: str = "sqlite:///./ai_life_planner.db"

    # Nunca uses este valor en producción: sobreescribir con JWT_SECRET_KEY.
    jwt_secret_key: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    environment: str = "development"

    # Orígenes permitidos para CORS, separados por coma — descubierto como
    # un hueco real al construir el frontend web (Módulo 5): sin esto, el
    # navegador bloquea toda llamada del frontend al backend por política
    # de mismo origen, incluso con credenciales/headers correctos. "*" es
    # deliberadamente permisivo para desarrollo; en producción esto DEBE
    # acotarse al dominio real del frontend (sección J del blueprint).
    cors_allowed_origins: str = "*"

    # Asistente con IA real (sección 16 del brief, ver app/assistant/llm_client.py).
    # None por default a propósito: sin key, el intérprete de intención cae
    # solo al motor basado en reglas (app/assistant/parser.py) — el
    # asistente sigue funcionando, solo que con el repertorio de frases más
    # chico de antes, nunca se cae ni exige la key para que el resto de la
    # app funcione.
    anthropic_api_key: str | None = None
    assistant_llm_model: str = "claude-haiku-4-5-20251001"


@lru_cache
def get_settings() -> Settings:
    return Settings()
