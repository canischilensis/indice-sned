from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_prefix: str = "/api/v1"
    api_cors_origins: str = "http://localhost:5173"
    api_entorno: str = "desarrollo"

    jwt_secret_key: str = "clave-insegura-solo-desarrollo"
    jwt_algoritmo: str = "HS256"
    jwt_minutos_expiracion: int = 480

    motor_por_defecto: str = "desagregado"
    xai_muestra_shap: int = 500

    database_url: str = "postgresql+psycopg://sned:cambiar-en-local@localhost:5432/indice_sned"

    @property
    def origenes_cors(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def config() -> Configuracion:
    return Configuracion()
