"""Adaptador de Gemini.

Lo que se puede verificar sin clave y sin red es casi todo lo que puede fallar
en silencio: la traduccion del esquema, el conteo de tokens, la lectura de la
respuesta y los dos modos de fallo de construccion. Lo unico que queda sin
verificar es la llamada viva, y esta declarado como tal en AGENTE_ASESOR.md.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from q5_agente.errores import ProveedorNoConfigurado
from q5_agente.fabrica import PROVEEDORES
from q5_agente.proveedores.externos import (
    AdaptadorGemini,
    _a_declaracion_gemini,
    _a_esquema_gemini,
)

CLAVE_FALSA = "clave-de-prueba"

ESQUEMA_DEL_ESCENARIO = {
    "type": "object",
    "properties": {
        "rbd": {"type": "string", "description": "Rol Base de Datos"},
        "variables": {
            "type": "object",
            "description": "Mapa variable -> valor.",
            "additionalProperties": {"type": "number"},
        },
        "factor": {"type": "string", "enum": ["EFECTIVR", "SUPERACR"]},
    },
    "required": ["rbd", "variables"],
}


# --- traduccion del esquema (sin SDK, sin clave) ---------------------------


def test_los_nombres_de_parametro_sobreviven_a_la_poda():
    """Regresion de un defecto real.

    La primera version podaba `properties` con la misma regla que el resto del
    esquema, de modo que 'rbd', 'variables' y 'factor' —que son nombres de
    parametro, no palabras del esquema— desaparecian. El adaptador declaraba
    entonces tres funciones sin ningun argumento.
    """
    podado = _a_esquema_gemini(ESQUEMA_DEL_ESCENARIO)
    assert sorted(podado["properties"]) == ["factor", "rbd", "variables"]
    assert podado["required"] == ["rbd", "variables"]
    assert podado["properties"]["factor"]["enum"] == ["EFECTIVR", "SUPERACR"]


def test_additional_properties_se_elimina_y_se_explica_en_prosa():
    """Gemini admite un subconjunto de OpenAPI, no JSON Schema completo."""
    variables = _a_esquema_gemini(ESQUEMA_DEL_ESCENARIO)["properties"]["variables"]
    assert "additionalProperties" not in variables
    assert variables["type"] == "object"
    assert "number" in variables["description"], "la restriccion perdida debe quedar dicha"


def test_el_catalogo_no_se_deforma_para_acomodar_al_proveedor():
    """La traduccion es del adaptador; el esquema original queda intacto."""
    antes = dict(ESQUEMA_DEL_ESCENARIO["properties"]["variables"])
    _a_declaracion_gemini(
        {"nombre": "x", "descripcion": "y", "esquema": ESQUEMA_DEL_ESCENARIO}
    )
    assert ESQUEMA_DEL_ESCENARIO["properties"]["variables"] == antes


def test_la_declaracion_lleva_nombre_descripcion_y_parametros():
    decl = _a_declaracion_gemini(
        {"nombre": "simulacion", "descripcion": "estima", "esquema": ESQUEMA_DEL_ESCENARIO}
    )
    assert set(decl) == {"name", "description", "parameters"}
    assert decl["name"] == "simulacion"


# --- conteo de tokens (sin SDK) --------------------------------------------


def test_el_razonamiento_se_cuenta_como_salida():
    """Omitirlo haria que la instrumentacion declare menos de lo que se gasta."""
    respuesta = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=900, candidates_token_count=120, thoughts_token_count=400
        )
    )
    assert AdaptadorGemini._contar(respuesta) == (900, 520)


def test_una_respuesta_sin_metadatos_de_uso_no_revienta():
    assert AdaptadorGemini._contar(SimpleNamespace()) == (0, 0)


def test_las_partes_se_leen_sin_tocar_punto_texto():
    """`respuesta.text` lanza cuando la respuesta es solo una llamada a funcion."""
    parte = SimpleNamespace(function_call=SimpleNamespace(name="f", args={"rbd": "1"}))
    respuesta = SimpleNamespace(
        candidates=[SimpleNamespace(content=SimpleNamespace(parts=[parte]))]
    )
    assert AdaptadorGemini._partes(respuesta) == [parte]
    assert AdaptadorGemini._partes(SimpleNamespace(candidates=[])) == []


# --- registro ---------------------------------------------------------------


def test_el_proveedor_esta_en_el_registro_explicito():
    assert "gemini" in PROVEEDORES


# --- construccion: los dos modos de fallo -----------------------------------


def test_sin_el_paquete_falla_al_construir_y_no_a_media_consulta(monkeypatch):
    class Bloqueador:
        def find_spec(self, nombre, ruta=None, destino=None):
            if nombre.split(".")[0] == "google":
                raise ImportError("bloqueado por la prueba")
            return None

    monkeypatch.setattr(sys, "meta_path", [Bloqueador(), *sys.meta_path])
    for modulo in [m for m in sys.modules if m.split(".")[0] == "google"]:
        monkeypatch.delitem(sys.modules, modulo, raising=False)

    with pytest.raises(ProveedorNoConfigurado, match="google-genai"):
        AdaptadorGemini(clave=CLAVE_FALSA)


def test_sin_clave_el_mensaje_distingue_la_suscripcion_de_la_api(monkeypatch):
    pytest.importorskip("google.genai")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ProveedorNoConfigurado) as excepcion:
        AdaptadorGemini()
    assert "AI Studio" in str(excepcion.value)


# --- precio por modelo ------------------------------------------------------


def test_el_precio_depende_del_modelo(monkeypatch):
    pytest.importorskip("google.genai")
    monkeypatch.setenv("GEMINI_API_KEY", CLAVE_FALSA)
    barato = AdaptadorGemini("gemini-2.5-flash-lite")
    caro = AdaptadorGemini("gemini-2.5-pro")
    assert barato.costo(1_000_000, 1_000_000) < caro.costo(1_000_000, 1_000_000)
    assert barato.precio_declarado is True


def test_un_modelo_sin_tarifa_conocida_declara_que_no_la_tiene(monkeypatch):
    """Preferible a inventar una tarifa: el costo cero queda marcado como tal."""
    pytest.importorskip("google.genai")
    monkeypatch.setenv("GEMINI_API_KEY", CLAVE_FALSA)
    adaptador = AdaptadorGemini("gemini-modelo-que-no-existe")
    assert adaptador.precio_declarado is False
    assert adaptador.costo(1_000_000, 1_000_000) == 0.0
    assert adaptador.describir()["precio_declarado"] is False


# --- lectura de la respuesta ------------------------------------------------


class _ClienteFalso:
    """Doble del cliente de la SDK. No hay red en esta prueba."""

    def __init__(self, partes, uso):
        self._partes, self._uso = partes, uso
        self.vistas: list[dict] = []
        self.models = SimpleNamespace(generate_content=self._generar)

    def _generar(self, *, model, contents, config):
        self.vistas.append({"model": model, "contents": contents, "config": config})
        return SimpleNamespace(
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=self._partes))],
            usage_metadata=self._uso,
        )


def _adaptador_con(partes, uso, monkeypatch):
    pytest.importorskip("google.genai")
    monkeypatch.setenv("GEMINI_API_KEY", CLAVE_FALSA)
    adaptador = AdaptadorGemini()
    adaptador._cliente = _ClienteFalso(partes, uso)  # noqa: SLF001
    return adaptador


def _herramientas():
    return [{"nombre": "diagnostico", "descripcion": "d", "esquema": ESQUEMA_DEL_ESCENARIO}]


def test_una_llamada_a_funcion_se_traduce_a_peticion_de_herramienta(monkeypatch):
    from q5_agente.proveedores.contrato import Mensaje

    parte = SimpleNamespace(
        function_call=SimpleNamespace(name="diagnostico", args={"rbd": "25520"}), text=None
    )
    uso = SimpleNamespace(
        prompt_token_count=50, candidates_token_count=10, thoughts_token_count=5
    )
    adaptador = _adaptador_con([parte], uso, monkeypatch)

    respuesta = adaptador.completar(
        [Mensaje("sistema", "instruccion"), Mensaje("usuario", "diagnostico del 25520")],
        _herramientas(),
    )

    assert respuesta.quiere_herramienta
    assert respuesta.peticion.nombre == "diagnostico"
    assert respuesta.peticion.parametros == {"rbd": "25520"}
    assert (respuesta.tokens_entrada, respuesta.tokens_salida) == (50, 15)


def test_el_mensaje_de_sistema_no_viaja_en_la_conversacion(monkeypatch):
    """Gemini lo quiere en system_instruction; mandarlo como turno lo degrada."""
    from q5_agente.proveedores.contrato import Mensaje

    parte = SimpleNamespace(function_call=None, text="texto final")
    adaptador = _adaptador_con([parte], SimpleNamespace(), monkeypatch)

    respuesta = adaptador.completar(
        [Mensaje("sistema", "usted es un asesor"), Mensaje("usuario", "hola")], _herramientas()
    )

    enviado = adaptador._cliente.vistas[0]  # noqa: SLF001
    assert len(enviado["contents"]) == 1, "el mensaje de sistema no es un turno"
    assert enviado["config"].system_instruction == "usted es un asesor"
    assert respuesta.texto == "texto final"
    assert not respuesta.quiere_herramienta


def test_el_rol_del_asistente_se_traduce_a_model(monkeypatch):
    from q5_agente.proveedores.contrato import Mensaje

    parte = SimpleNamespace(function_call=None, text="ok")
    adaptador = _adaptador_con([parte], SimpleNamespace(), monkeypatch)
    adaptador.completar(
        [Mensaje("usuario", "a"), Mensaje("asistente", "b"), Mensaje("herramienta", "c")],
        _herramientas(),
    )
    roles = [c.role for c in adaptador._cliente.vistas[0]["contents"]]  # noqa: SLF001
    assert roles == ["user", "model", "user"]


# --- la familia de modelos rota --------------------------------------------


def test_un_modelo_retirado_es_configuracion_y_no_una_caida(monkeypatch):
    """Nace de un fallo real: gemini-2.5-flash quedo cerrado a claves nuevas.

    Se traduce a ProveedorNoConfigurado y no a ErrorDelProveedor porque el
    cortacircuitos (G-04) protege de un proveedor caido, y reintentar contra un
    modelo que no existe nunca va a funcionar. Tratarlo como caida haria que
    tres consultas mal configuradas abrieran el circuito y taparan la causa.
    """
    from q5_agente.errores import ProveedorNoConfigurado

    class ClienteQueNiega:
        def __init__(self):
            self.models = SimpleNamespace(generate_content=self._negar)

        def _negar(self, **_):
            raise RuntimeError(
                "404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model "
                "models/gemini-2.5-flash is no longer available to new users.'}}"
            )

    pytest.importorskip("google.genai")
    monkeypatch.setenv("GEMINI_API_KEY", CLAVE_FALSA)
    adaptador = AdaptadorGemini("gemini-2.5-flash")
    adaptador._cliente = ClienteQueNiega()  # noqa: SLF001

    from q5_agente.proveedores.contrato import Mensaje

    with pytest.raises(ProveedorNoConfigurado) as excepcion:
        adaptador.completar([Mensaje("usuario", "hola")], _herramientas())
    assert "AGENTE_MODELO" in str(excepcion.value)
    assert "gemini-2.5-flash" in str(excepcion.value)


def test_si_el_modelo_rechaza_temperature_se_reintenta_sin_ella(monkeypatch):
    """La linea 3.x deprecia los parametros de muestreo. Se cede el parametro,
    no la consulta, y el adaptador lo recuerda para no gastar dos llamadas cada
    vez."""
    from q5_agente.proveedores.contrato import Mensaje

    class ClienteQuisquilloso:
        def __init__(self):
            self.configuraciones = []
            self.models = SimpleNamespace(generate_content=self._generar)

        def _generar(self, *, model, contents, config):
            self.configuraciones.append(config)
            if getattr(config, "temperature", None) is not None:
                raise RuntimeError("400 INVALID_ARGUMENT: temperature is not supported")
            return SimpleNamespace(
                candidates=[
                    SimpleNamespace(
                        content=SimpleNamespace(
                            parts=[SimpleNamespace(function_call=None, text="listo")]
                        )
                    )
                ],
                usage_metadata=SimpleNamespace(),
            )

    pytest.importorskip("google.genai")
    monkeypatch.setenv("GEMINI_API_KEY", CLAVE_FALSA)
    adaptador = AdaptadorGemini()
    adaptador._cliente = ClienteQuisquilloso()  # noqa: SLF001

    assert adaptador.completar([Mensaje("usuario", "a")], _herramientas()).texto == "listo"
    assert len(adaptador._cliente.configuraciones) == 2, "una con muestreo y el reintento"  # noqa: SLF001

    adaptador.completar([Mensaje("usuario", "b")], _herramientas())
    assert len(adaptador._cliente.configuraciones) == 3, "ya no reintenta: lo recordo"  # noqa: SLF001
