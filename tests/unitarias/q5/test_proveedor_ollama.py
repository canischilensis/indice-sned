"""El adaptador de un modelo local: traduccion verificada sin levantar Ollama.

Probar contra un servidor real solo diria que Ollama funciona. Lo que hay que
verificar es que **la traduccion entre su API y el puerto sea correcta**, y eso
se comprueba con respuestas fijas, sin descargar cinco gigabytes ni depender de
que el servicio este arriba.

Lo que estas pruebas NO cubren, y se declara: la calidad del ruteo de un modelo
de ocho mil millones de parametros. Eso se mide con el arnes, contra un Ollama de
verdad, y el resultado puede ser peor que el de un modelo de frontera. Si lo es,
ese es el hallazgo.
"""

from __future__ import annotations

import httpx
import pytest
from q5_agente.errores import ErrorDelProveedor, ProveedorNoConfigurado
from q5_agente.proveedores.contrato import Mensaje, ProveedorDeModelo
from q5_agente.proveedores.ollama import AdaptadorOllama

pytestmark = pytest.mark.agente

HERRAMIENTAS = [
    {
        "nombre": "diagnostico_de_establecimiento",
        "descripcion": "Estado del establecimiento",
        "esquema": {"type": "object", "properties": {"rbd": {"type": "string"}}},
    }
]


def _adaptador(responder) -> AdaptadorOllama:
    return AdaptadorOllama(cliente=httpx.Client(transport=httpx.MockTransport(responder)))


def _respuesta(carga: dict, codigo: int = 200):
    return lambda peticion: httpx.Response(codigo, json=carga)


class TestContrato:
    def test_implementa_el_puerto(self):
        assert isinstance(AdaptadorOllama(), ProveedorDeModelo)

    def test_declara_costo_cero_y_ejecucion_local(self):
        descripcion = AdaptadorOllama().describir()

        assert descripcion["usd_por_millon_entrada"] == 0.0
        assert "no sale de la maquina" in descripcion["ejecucion"]

    def test_no_necesita_ningun_sdk(self):
        """El unico proveedor que no agrega dependencias: habla HTTP con httpx."""
        import q5_agente.proveedores.ollama as modulo

        assert not hasattr(modulo, "openai")
        assert modulo.httpx is httpx


class TestTraduccion:
    def test_una_llamada_a_herramienta_se_traduce_a_peticion(self):
        adaptador = _adaptador(
            _respuesta(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "diagnostico_de_establecimiento",
                                    "arguments": {"rbd": "25520"},
                                }
                            }
                        ],
                    },
                    "prompt_eval_count": 1200,
                    "eval_count": 48,
                }
            )
        )

        respuesta = adaptador.completar([Mensaje("usuario", "diagnostico")], HERRAMIENTAS)

        assert respuesta.quiere_herramienta
        assert respuesta.peticion.nombre == "diagnostico_de_establecimiento"
        assert respuesta.peticion.parametros == {"rbd": "25520"}
        assert respuesta.tokens_entrada == 1200
        assert respuesta.tokens_salida == 48

    def test_los_argumentos_como_cadena_json_tambien_se_aceptan(self):
        """Algunas plantillas devuelven la cadena en vez del objeto.

        Rechazar la segunda forma seria descartar una respuesta correcta por su
        envoltorio, y el modelo no elige como su plantilla serializa.
        """
        adaptador = _adaptador(
            _respuesta(
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "diagnostico_de_establecimiento",
                                    "arguments": '{"rbd": "9012"}',
                                }
                            }
                        ]
                    }
                }
            )
        )

        respuesta = adaptador.completar([Mensaje("usuario", "x")], HERRAMIENTAS)

        assert respuesta.peticion.parametros == {"rbd": "9012"}

    def test_un_texto_final_se_traduce_como_texto(self):
        adaptador = _adaptador(_respuesta({"message": {"content": "El indice es 69,36."}}))

        respuesta = adaptador.completar([Mensaje("usuario", "x")], [])

        assert not respuesta.quiere_herramienta
        assert "69,36" in respuesta.texto

    def test_la_observacion_viaja_con_el_rol_tool(self):
        """Ollama distingue ese rol; usarlo entrega la conversacion como su plantilla espera."""
        visto: dict = {}

        def responder(peticion):
            import json as _json

            visto.update(_json.loads(peticion.content))
            return httpx.Response(200, json={"message": {"content": "ok"}})

        _adaptador(responder).completar(
            [Mensaje("sistema", "s"), Mensaje("usuario", "u"), Mensaje("herramienta", "obs")], []
        )

        assert [m["role"] for m in visto["messages"]] == ["system", "user", "tool"]


class TestFallos:
    def test_sin_servidor_dice_como_instalarlo(self):
        def responder(peticion):
            raise httpx.ConnectError("conexion rechazada")

        with pytest.raises(ProveedorNoConfigurado, match="ollama pull"):
            _adaptador(responder).completar([Mensaje("usuario", "x")], [])

    def test_un_modelo_ausente_dice_como_descargarlo(self):
        adaptador = _adaptador(_respuesta({"error": "model not found"}, codigo=404))

        with pytest.raises(ProveedorNoConfigurado, match="qwen3:8b"):
            adaptador.completar([Mensaje("usuario", "x")], [])

    def test_otro_error_del_servidor_es_error_del_proveedor(self):
        """Distinguir configuracion de caida importa: solo la segunda abre el cortacircuitos."""
        adaptador = _adaptador(_respuesta({"error": "roto"}, codigo=500))

        with pytest.raises(ErrorDelProveedor):
            adaptador.completar([Mensaje("usuario", "x")], [])
