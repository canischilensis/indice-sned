"""La credencial del proveedor se lee del .env, y no entra en la configuracion.

Nace de un defecto real y silencioso: `.env.example` documentaba GEMINI_API_KEY
dentro del .env, pero el adaptador consultaba solo `os.environ`. La clave escrita
en el archivo se ignoraba, y el agente respondia que faltaba una variable que el
usuario ya habia puesto. Un fallo asi cuesta una tarde, porque el mensaje de
error contradice lo que la persona esta viendo en pantalla.
"""

from __future__ import annotations

from q5_agente.config import ConfiguracionDelAgente, secreto

CLAVE = "clave-de-prueba-abc123"


def _env(tmp_path, contenido: str):
    archivo = tmp_path / ".env"
    archivo.write_text(contenido, encoding="utf-8")
    return archivo


def test_la_clave_puesta_en_el_env_se_encuentra(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    archivo = _env(tmp_path, f"AGENTE_PROVEEDOR=gemini\nGEMINI_API_KEY={CLAVE}\n")
    assert secreto("GEMINI_API_KEY", archivo) == CLAVE


def test_la_variable_del_proceso_manda_sobre_el_archivo(tmp_path, monkeypatch):
    """Misma precedencia que el resto de la configuracion, sin excepciones."""
    monkeypatch.setenv("GEMINI_API_KEY", "la-del-proceso")
    archivo = _env(tmp_path, f"GEMINI_API_KEY={CLAVE}\n")
    assert secreto("GEMINI_API_KEY", archivo) == "la-del-proceso"


def test_sin_clave_en_ninguna_parte_devuelve_none(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert secreto("GEMINI_API_KEY", _env(tmp_path, "AGENTE_PROVEEDOR=gemini\n")) is None


def test_una_clave_vacia_cuenta_como_ausente(tmp_path, monkeypatch):
    """`GEMINI_API_KEY=` sin valor es una linea a medio llenar, no una clave."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert secreto("GEMINI_API_KEY", _env(tmp_path, "GEMINI_API_KEY=\n")) is None


def test_la_credencial_no_entra_en_la_configuracion(tmp_path, monkeypatch):
    """No es un parametro de operacion: no debe describirse ni trazarse.

    La ruta /salud publica la configuracion. Si la clave viviera dentro del
    objeto, bastaria un `repr` en una traza para filtrarla.
    """
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    archivo = _env(tmp_path, f"AGENTE_PROVEEDOR=gemini\nGEMINI_API_KEY={CLAVE}\n")
    cfg = ConfiguracionDelAgente.desde_entorno(archivo)

    assert cfg.agente_proveedor == "gemini", "lo que si es configuracion, se lee"
    assert CLAVE not in repr(cfg)
    assert not any("key" in campo.lower() for campo in vars(cfg))
