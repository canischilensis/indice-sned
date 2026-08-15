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
    cifras_del_contexto,
)
from q5_agente.errores import (
    CircuitoAbierto,
    ErrorDelProveedor,
    ParametroInvalido,
    RespuestaRechazada,
)
from q5_agente.guardarrailes import PoliticaDeSalida
from q5_agente.herramientas.contrato import Herramienta, Procedencia, ResultadoHerramienta
from q5_agente.prompts import CIERRE, SISTEMA, formatear_consulta
from q5_agente.proveedores.contrato import Mensaje, ProveedorDeModelo
from q5_agente.redaccion import a_prosa_plana

_DISCULPA_PROVEEDOR = (
    "No puedo redactar la respuesta porque el proveedor de lenguaje no esta disponible en este "
    "momento. Los datos del servicio siguen accesibles desde el tablero y el reporte de "
    "explicabilidad."
)


#: Se mantiene el nombre local por compatibilidad con el resto del modulo. La
#: funcion se mudo a `contrato.py` cuando aparecio el segundo adaptador del
#: puerto: es una regla del dominio —que cuentan como respaldadas las cifras del
#: propio pedido— y no una particularidad de este bucle. Los dos orquestadores
#: deben aplicarla identica, o la comparacion entre ambos mediria dos politicas
#: distintas en vez de dos formas de orquestar.
_cifras_del_contexto = cifras_del_contexto


def _numero(valor: Any) -> float | None:
    """Convierte a magnitud lo que sea magnitud, y descarta el resto."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int | float):
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
        # Conjunto aparte: magnitudes que aparecen en mensajes del sistema. Se
        # admiten al validar, pero no se presentan como evidencia de dato.
        diagnostico: set[float] = set()
        documentales: set[float] = set()
        procedencias: list[Procedencia] = []
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
                return self._cerrar(
                    paso.texto or "", llamadas, cifras, uso, diagnostico,
                    documentales, procedencias,
                )

            resultado, registro = self._ejecutar(
                paso.peticion.nombre, paso.peticion.parametros, consulta
            )
            llamadas.append(registro)
            cifras |= resultado.cifras
            cifras |= _cifras_de_parametros(registro.parametros)
            diagnostico |= resultado.cifras_diagnostico
            # Tercer conjunto: no se mezcla con el primero a proposito. Una cifra
            # leida de un documento no es una medicion, y G-02 exige que el texto
            # nombre el documento antes de aceptarla.
            documentales |= resultado.cifras_documentales
            procedencias.extend(resultado.procedencias)
            mensajes.append(
                Mensaje("herramienta", json.dumps(self._observacion(resultado), ensure_ascii=False))
            )

        # Agotado el presupuesto de herramientas, queda un turno de redaccion
        # SIN catalogo. Nace de un fallo real con un proveedor externo: una
        # llamada rechazada por parametro consumio un paso, el reintento otro, y
        # el bucle se quedo sin turno para escribir pese a tener ya los datos en
        # la mano. Devolver "no consegui cerrar la consulta" con la respuesta
        # practicamente servida es desperdiciar el trabajo y el gasto.
        #
        # El turno de cierre no puede pedir herramientas —se le entrega catalogo
        # vacio—, de modo que el limite de llamadas al servicio se respeta: lo
        # que se concede es redactar, no seguir consultando.
        if llamadas:
            try:
                final = self._proveedor.completar([*mensajes, Mensaje("usuario", CIERRE)], [])
            except (CircuitoAbierto, ErrorDelProveedor):
                final = None
            if final is not None:
                uso = uso.mas(
                    Uso(
                        tokens_entrada=final.tokens_entrada,
                        tokens_salida=final.tokens_salida,
                        costo_usd=self._proveedor.costo(
                            final.tokens_entrada, final.tokens_salida
                        ),
                        llamadas_al_modelo=1,
                    )
                )
                if not final.quiere_herramienta and (final.texto or "").strip():
                    return self._cerrar(
                        final.texto or "", llamadas, cifras, uso, diagnostico,
                        documentales, procedencias,
                    )

        return self._cerrar(
            "No consegui cerrar la consulta dentro del limite de pasos previsto.",
            llamadas,
            cifras,
            uso,
            diagnostico,
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
        diagnostico: set[float] | None = None,
        documentales: set[float] | None = None,
        procedencias: list[Procedencia] | None = None,
    ) -> RespuestaAsesor:
        # La normalizacion va ANTES de la politica, no despues: el guardarrail
        # debe juzgar exactamente el texto que se entrega. Validar una version y
        # mostrar otra deja un hueco por donde no mira nadie.
        texto = a_prosa_plana(texto)
        documentos = tuple(dict.fromkeys(p.documento for p in (procedencias or [])))
        aceptado, codigo, motivo = self._politica.evaluar(
            texto, cifras | (diagnostico or set()), documentales or set(), documentos
        )
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
            cifras_de_diagnostico=sorted(diagnostico or set()),
            cifras_documentales=sorted(documentales or set()),
            documentos_consultados=list(documentos),
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
