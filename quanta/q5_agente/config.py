"""Configuracion del cuanto 5. Todo por variable de entorno, nada codificado."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfiguracionDelAgente(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    #: Servicio del indice (Q3). El agente lo consulta como cualquier usuario.
    agente_base_url: str = "http://127.0.0.1:8000"
    agente_prefijo_api: str = "/api/v1"
    agente_usuario: str = "sostenedor.demo"
    agente_clave: str = "demo"
    agente_segundos_espera: float = 10.0

    #: Proveedor de lenguaje: determinista | anthropic | openai
    agente_proveedor: str = "determinista"
    agente_modelo: str = ""

    #: Bucle y cortacircuitos
    agente_max_pasos: int = 3
    agente_umbral_fallos: int = 3
    agente_segundos_reposo: float = 30.0

    #: Guardarrailes (se pueden apagar solo en pruebas, nunca en operacion)
    agente_guardarrail_cifras: bool = True
    agente_guardarrail_promesas: bool = True


@lru_cache(maxsize=1)
def config_agente() -> ConfiguracionDelAgente:
    return ConfiguracionDelAgente()
