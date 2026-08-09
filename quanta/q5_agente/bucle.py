"""Bucle de ejecucion simple: el adaptador de referencia del puerto AsesorDeGestion.

Observa la consulta, decide una herramienta, la ejecuta, observa el resultado y
responde. Se empieza por lo simple: escalar a planificacion explicita de varios
pasos solo se justificaria con evidencia de que la complejidad lo exige, y esa
evidencia todavia no existe.

El bucle tiene tres limites duros:
  - un maximo de pasos, para que no gire indefinidamente;
  - los guardarrailes de salida, que pueden rechazar el texto ya generado;
  - la jurisdiccion, que no vive aqui sino en el servicio: el agente consulta
    las rutas publicadas y recibe 403 como cualquier usuario.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from q5_agente.contrato import (
    AsesorDeGestion,
    Consulta,
    LlamadaHerramienta,
    RespuestaAsesor,
    Uso,
)
from q5_agente.errores import (
    CircuitoAbierto,
    ErrorDelProveedor,
    ParametroInvalido,
    RespuestaRechazada,
)
from q5_agente.guardarrailes import PoliticaDeSalida
from q5_agente.herramientas.contrato import Herramienta, ResultadoHerramienta
from q5_agente.prompts import SISTEMA, formatear_consulta
from q5_agente.proveedores.contrato import Mensaje, ProveedorDeModelo

_DISCULPA_PROVEEDOR = (
    "No puedo redactar la respuesta porque el proveedor de lenguaje no esta disponible en este "
    "momento. Los datos del servicio siguen accesibles desde el tablero y el reporte de "
    "explicabilidad."
)


def _cifras_del_contexto(consulta: Consulta) -> set[float]:
    """Magnitudes que el propio pedido aporta: identificador y bienio."""
    cifras: set[float] = set()
    if consulta.rbd.isdigit():
        cifras.add(float(consulta.rbd))
    if consulta.periodo:
        for parte in consulta.periodo.split("-"):
            if parte.isdigit():
                cifras.add(float(parte))
    return cifras


def _numero(valor: Any) -> float | None:
    """Convierte a magnitud lo que sea magnitud, y descarta el resto."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str) and valor.isdigit():
        return float(valor)
    return None


def _cifras_de_parametros(parametros: dict[str, Any]) -> set[float]:
    """Valores que el directivo fijo en el escenario. Tampoco son invencion."""
    cifras: set[float] = set()
    for clave, valor in parametros.items():
        if clave == "variables" and isinstance(valor, dict):
            cifras |= {n for n in map(_numero, valor.values()) if n is not None}
            continue
        numero = _numero(valor)
        if numero is not None:
            cifras.add(numero)
    return cifras


class AgenteDeBucleSimple(AsesorDeGestion):
    """Implementacion del puerto mediante un bucle de una sola rama."""

    nombre = "bucle_simple"

    def __init__(
        self,
        proveedor: ProveedorDeModelo,
        herramientas: dict[str, Herramienta],
        politica: PoliticaDeSalida | None = None,
        max_pasos: int = 3,
        reloj: Callable[[], float] | None = None,
    ) -> None:
        self._proveedor = proveedor
        self._herramientas = herramientas
        self._politica = politica or PoliticaDeSalida()
        self._max_pasos = max_pasos
        self._reloj = reloj or time.monotonic

    # --- puerto -----------------------------------------------------------

    def asesorar(self, consulta: Consulta) -> RespuestaAsesor:
        mensajes = [
            Mensaje("sistema", SISTEMA),
            Mensaje("usuario", formatear_consulta(consulta)),
        ]
        catalogo = [
            {"nombre": h.nombre, "descripcion": h.descripcion, "esquema": h.esquema()}
            for h in self._herramientas.values()
        ]

        llamadas: list[LlamadaHerramienta] = []
        # Las cifras del propio pedido (el RBD, el bienio, los valores que el
        # directivo fijo) no son invencion del modelo: son dato de la sesion, y
        # el agente debe poder repetirlas al explicar un error.
        cifras: set[float] = _cifras_del_contexto(consulta)
        uso = Uso()

        for _ in range(self._max_pasos):
            try:
                paso = self._proveedor.completar(mensajes, catalogo)
            except (CircuitoAbierto, ErrorDelProveedor) as exc:
                return RespuestaAsesor(
                    texto=f"{_DISCULPA_PROVEEDOR} Motivo tecnico: {exc}",
                    llamadas=llamadas,
                    uso=uso,
                    guardarrailes_aplicados=["G-04"],
                    rechazada=True,
                    motivo_rechazo=str(exc),
                )

            uso = uso.mas(
                Uso(
                    tokens_entrada=paso.tokens_entrada,
                    tokens_salida=paso.tokens_salida,
                    costo_usd=self._proveedor.costo(paso.tokens_entrada, paso.tokens_salida),
                    llamadas_al_modelo=1,
                )
            )

            if not paso.quiere_herramienta:
                return self._cerrar(paso.texto or "", llamadas, cifras, uso)

            resultado, registro = self._ejecutar(
                paso.peticion.nombre, paso.peticion.parametros, consulta
            )
            llamadas.append(registro)
            cifras |= resultado.cifras
            cifras |= _cifras_de_parametros(registro.parametros)
            mensajes.append(
                Mensaje("herramienta", json.dumps(self._observacion(resultado), ensure_ascii=False))
            )

        return self._cerrar(
            "No consegui cerrar la consulta dentro del limite de pasos previsto.",
            llamadas,
            cifras,
            uso,
        )

    # --- ejecucion de herramientas ---------------------------------------

    def _ejecutar(
        self, nombre: str, parametros: dict[str, Any], consulta: Consulta
    ) -> tuple[ResultadoHerramienta, LlamadaHerramienta]:
        herramienta = self._herramientas.get(nombre)
        inicio = self._reloj()
        if herramienta is None:
            resultado = ResultadoHerramienta.fallida(
                nombre, f"Herramienta '{nombre}' inexistente."
            )
            registro = LlamadaHerramienta(nombre, parametros, False, resultado.error or "", 0)
            return resultado, registro

        # El RBD de la sesion manda sobre el que el modelo haya podido inferir.
        efectivos = dict(parametros)
        efectivos["rbd"] = consulta.rbd
        if consulta.periodo and not efectivos.get("periodo"):
            efectivos["periodo"] = consulta.periodo

        try:
            resultado = herramienta.ejecutar(**efectivos)
        except ParametroInvalido as exc:
            resultado = ResultadoHerramienta.fallida(nombre, str(exc))

        transcurrido = int((self._reloj() - inicio) * 1000)
        registro = LlamadaHerramienta(
            herramienta=nombre,
            parametros=efectivos,
            exito=resultado.exito,
            resumen=resultado.error or f"{len(resultado.cifras)} cifras recibidas",
            milisegundos=transcurrido,
        )
        return resultado, registro

    @staticmethod
    def _observacion(resultado: ResultadoHerramienta) -> dict[str, Any]:
        return {
            "herramienta": resultado.herramienta,
            "exito": resultado.exito,
            "error": resultado.error,
            "origen": resultado.origen,
            "datos": resultado.datos,
        }

    # --- cierre con guardarrailes ----------------------------------------

    def _cerrar(
        self,
        texto: str,
        llamadas: list[LlamadaHerramienta],
        cifras: set[float],
        uso: Uso,
    ) -> RespuestaAsesor:
        aceptado, codigo, motivo = self._politica.evaluar(texto, cifras)
        if not aceptado:
            return RespuestaAsesor(
                texto=(
                    "Retire la respuesta antes de entregarla porque no cumplia la politica de "
                    "salida del sistema. Puede consultar las cifras directamente en el tablero."
                ),
                llamadas=llamadas,
                uso=uso,
                guardarrailes_aplicados=[codigo or "G-00"],
                rechazada=True,
                motivo_rechazo=motivo,
            )
        return RespuestaAsesor(
            texto=texto,
            llamadas=llamadas,
            uso=uso,
            cifras_citadas=sorted(cifras),
            guardarrailes_aplicados=["G-01", "G-02", "G-03"],
        )

    def describir(self) -> dict[str, Any]:
        return {
            "asesor": self.nombre,
            "proveedor": self._proveedor.describir(),
            "herramientas": sorted(self._herramientas),
            "max_pasos": self._max_pasos,
        }


def exigir_respuesta(respuesta: RespuestaAsesor) -> RespuestaAsesor:
    """Convierte un rechazo en excepcion, para quien prefiera fallar temprano."""
    if respuesta.rechazada:
        raise RespuestaRechazada(
            respuesta.motivo_rechazo or "Respuesta rechazada por politica.",
            (respuesta.guardarrailes_aplicados or ["G-00"])[0],
        )
    return respuesta
