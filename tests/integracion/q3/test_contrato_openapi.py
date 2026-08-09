"""INT-04 · El contrato entre el cuanto 3 y el cuanto 4.

La interfaz consume JSON tipado y no conoce el algoritmo que hay detras. Esa
opacidad solo se sostiene si el contrato se respeta, y aqui se verifica contra
el esquema OpenAPI que la propia API declara: no contra una copia a mano que
puede quedar desactualizada.

Tecnica de diseno: prueba de contrato (ISO/IEC/IEEE 29119-4).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

jsonschema = pytest.importorskip("jsonschema", reason="jsonschema no instalado")

from q3_servicio.main import app  # noqa: E402

pytestmark = pytest.mark.api

CLIENTE = TestClient(app)
ESQUEMA = app.openapi()


def _validar(cuerpo, ruta: str, metodo: str = "get", codigo: str = "200") -> None:
    """Valida el cuerpo contra el esquema que la API declara para esa ruta."""
    operacion = ESQUEMA["paths"][ruta][metodo]
    contenido = operacion["responses"][codigo].get("content")
    if contenido is None:
        return  # la operacion no declara cuerpo
    sub = contenido["application/json"]["schema"]
    # el esquema referencia components/schemas: se resuelve con el documento completo
    jsonschema.validate(
        instance=cuerpo,
        schema={**sub, "components": ESQUEMA.get("components", {})},
        resolver=jsonschema.RefResolver.from_schema(ESQUEMA),
    )


def _token() -> dict:
    r = CLIENTE.post("/api/v1/auth/token", data={"username": "auditor.demo", "password": "demo"})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------------------------------------------------------------------------
# El esquema existe y es coherente
# ---------------------------------------------------------------------------


def test_la_api_publica_su_esquema_openapi():
    r = CLIENTE.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["openapi"].startswith("3.")


def test_el_esquema_declara_los_endpoints_que_consume_la_interfaz():
    """Las tres ventanas del cuanto 4 dependen de estas rutas."""
    rutas = set(ESQUEMA["paths"])
    esperadas = {
        "/api/v1/prediccion/{rbd}",
        "/api/v1/prediccion/{rbd}/alertas",
        "/api/v1/xai/{rbd}/shapley",
        "/api/v1/xai/simular",
        "/api/v1/establecimientos",
    }
    faltan = esperadas - rutas
    assert not faltan, f"El contrato no declara: {sorted(faltan)}"


# Las seis rutas que consumen las tres ventanas del cuanto 4. Todas deben
# declarar un modelo de respuesta: un `additionalProperties: true` acepta
# cualquier cosa y no es un contrato, es la ausencia de uno.
RUTAS_DEL_CLIENTE = {
    ("get", "/api/v1/prediccion/{rbd}"),
    ("get", "/api/v1/prediccion/{rbd}/alertas"),
    ("get", "/api/v1/xai/{rbd}/shapley"),
    ("post", "/api/v1/xai/simular"),
    ("get", "/api/v1/establecimientos"),
    ("get", "/api/v1/establecimientos/{rbd}/ranking"),
}


def test_las_rutas_que_consume_la_interfaz_declaran_un_modelo_de_respuesta():
    """Un objeto libre no es un contrato: el cliente no puede generar tipos.

    Al escribir esta prueba se descubrio que dos de las seis rutas devolvian
    `dict` y quedaban sin tipar en el esquema. Se les agrego modelo.
    """
    sin_tipar = []
    for metodo, ruta in sorted(RUTAS_DEL_CLIENTE):
        esquema = (
            ESQUEMA["paths"][ruta][metodo]["responses"]["200"]["content"]
            ["application/json"]["schema"]
        )
        if "$ref" not in esquema:
            sin_tipar.append(f"{metodo.upper()} {ruta}")
    assert not sin_tipar, (
        "Estas rutas devuelven un objeto libre y la interfaz no puede tiparlas: "
        f"{sin_tipar}"
    )


def test_la_validacion_del_contrato_rechaza_cuerpos_que_no_cumplen():
    """Prueba de la prueba: si `_validar` aceptara cualquier cosa, seria inutil."""
    with pytest.raises(jsonschema.ValidationError):
        _validar({"rbd": "9"}, "/api/v1/establecimientos/{rbd}/ranking")
    with pytest.raises(jsonschema.ValidationError):
        _validar(
            {"rol": "auditor", "rbds": [], "origen": "parquet", "detalle": "no es lista"},
            "/api/v1/establecimientos",
        )


# ---------------------------------------------------------------------------
# Las respuestas reales cumplen el esquema declarado
# ---------------------------------------------------------------------------


def test_el_listado_de_establecimientos_cumple_su_contrato():
    r = CLIENTE.get("/api/v1/establecimientos", headers=_token())
    if r.status_code == 503:
        pytest.skip("Sin conjunto de datos disponible en este entorno.")
    assert r.status_code == 200
    _validar(r.json(), "/api/v1/establecimientos")


def test_el_esquema_de_prediccion_declara_la_frontera_de_informacion():
    """`es_acotado` y `restriccion` no son adorno: son el hallazgo central.

    Si desaparecen del contrato, la interfaz deja de poder advertir que el
    63 % de la ponderacion esta limitado por informacion no publica.
    """
    propiedades = ESQUEMA["components"]["schemas"]["FactorPredicho"]["properties"]
    for campo in ("es_acotado", "restriccion", "peso", "aporte_al_indice"):
        assert campo in propiedades, f"El contrato perdio el campo {campo}"


def test_el_esquema_de_prediccion_exige_la_advertencia_de_decision_humana():
    """El principio etico del proyecto, como campo obligatorio del contrato."""
    esquema = ESQUEMA["components"]["schemas"]["RespuestaPrediccion"]
    assert "advertencia" in esquema["properties"]
    assert "advertencia" in esquema.get("required", []), (
        "La advertencia debe ser obligatoria, no opcional: si el contrato "
        "permite omitirla, la interfaz puede mostrar una estimacion sin ella."
    )


def test_la_simulacion_exige_la_advertencia_de_magnitud():
    esquema = ESQUEMA["components"]["schemas"]["RespuestaSimulacion"]
    assert "advertencia_magnitud" in esquema["properties"]
    assert "advertencia_magnitud" in esquema.get("required", [])


def test_el_acceso_sin_token_esta_declarado_en_el_contrato():
    """El 401 tiene que estar en el esquema, no solo ocurrir en tiempo de ejecucion."""
    op = ESQUEMA["paths"]["/api/v1/prediccion/{rbd}"]["get"]
    assert "security" in op or "components" in ESQUEMA and "securitySchemes" in ESQUEMA["components"]
