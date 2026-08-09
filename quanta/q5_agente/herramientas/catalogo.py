"""Las tres herramientas del agente.

Cada una envuelve rutas existentes del servicio. Ninguna calcula: piden, reciben
y devuelven. El agente nunca pondera factores ni reconstruye el indice, porque
ese calculo vive en el cuanto 2 y ya esta verificado contra el oficial.

  1. diagnostico_de_establecimiento  GET /prediccion/{rbd}
                                     GET /prediccion/{rbd}/alertas
                                     GET /establecimientos/{rbd}/ranking
  2. explicacion_por_factor          GET /xai/{rbd}/shapley
  3. simulacion_de_escenario         POST /prediccion/{rbd}/escenario
"""

from __future__ import annotations

from typing import Any

from q5_agente.errores import ErrorDelServicio
from q5_agente.gateway import PuertaDeServicio
from q5_agente.guardarrailes import SanitizadorDeParametros
from q5_agente.herramientas.contrato import Herramienta, ResultadoHerramienta

FACTORES = ("EFECTIVR", "SUPERACR", "INICIATR", "MEJORAMR", "IGUALDAR", "INTEGRAR")


class _HerramientaConGateway(Herramienta):
    def __init__(self, puerta: PuertaDeServicio, sanitizador: SanitizadorDeParametros) -> None:
        self._puerta = puerta
        self._sanitizador = sanitizador


class DiagnosticoDeEstablecimiento(_HerramientaConGateway):
    """Estado actual: indice estimado, desglose por factor, alertas y posicion."""

    nombre = "diagnostico_de_establecimiento"
    descripcion = (
        "Entrega la estimacion del Indice SNED de un establecimiento, el desglose de sus seis "
        "factores con su ponderacion, las alertas tempranas vigentes y su posicion dentro del "
        "Grupo Homogeneo del periodo. Usela para responder que situacion tiene el establecimiento."
    )
    disparadores = (
        "diagnostico", "situacion", "estado", "como esta", "como estamos", "indice",
        "posicion", "ranking", "grupo homogeneo", "alerta", "riesgo", "resumen",
    )

    def esquema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rbd": {"type": "string", "description": "Rol Base de Datos del establecimiento"},
                "periodo": {"type": "string", "description": "Bienio, por ejemplo 2024-2025"},
            },
            "required": ["rbd"],
        }

    def ejecutar(self, **parametros: Any) -> ResultadoHerramienta:
        limpios = self._sanitizador.limpiar(self.nombre, parametros)
        rbd, periodo = limpios["rbd"], limpios.get("periodo")
        try:
            prediccion = self._puerta.obtener(f"/prediccion/{rbd}", {"periodo": periodo})
            alertas = self._puerta.obtener(f"/prediccion/{rbd}/alertas", {"periodo": periodo})
        except ErrorDelServicio as exc:
            return ResultadoHerramienta.fallida(self.nombre, str(exc))

        datos: dict[str, Any] = {"prediccion": prediccion, "alertas": alertas.get("alertas", [])}
        try:
            datos["posicion"] = self._puerta.obtener(
                f"/establecimientos/{rbd}/ranking", {"periodo": periodo}
            )
        except ErrorDelServicio as exc:
            # La posicion es complementaria: su ausencia no invalida el diagnostico.
            datos["posicion"] = None
            datos["nota_posicion"] = f"Posicion intragrupo no disponible: {exc}"

        return ResultadoHerramienta.desde(self.nombre, datos, origen="API del servicio SNED")


class ExplicacionPorFactor(_HerramientaConGateway):
    """Atribucion de Shapley sobre un factor, con verificacion de aditividad."""

    nombre = "explicacion_por_factor"
    descripcion = (
        "Descompone la estimacion de un factor en la contribucion individual de cada variable "
        "mediante valores de Shapley, e informa si la aditividad quedo verificada. Usela para "
        "responder por que el establecimiento obtuvo ese resultado en un factor."
    )
    disparadores = (
        "por que", "porque", "explica", "explicacion", "atribuc", "contribu",
        "shapley", "influye", "causa", "detona", "se cae", "factor",
    )

    def esquema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rbd": {"type": "string"},
                "factor": {"type": "string", "enum": list(FACTORES)},
                "periodo": {"type": "string"},
            },
            "required": ["rbd"],
        }

    def ejecutar(self, **parametros: Any) -> ResultadoHerramienta:
        limpios = self._sanitizador.limpiar(self.nombre, parametros)
        rbd = limpios["rbd"]
        consulta = {"factor": limpios.get("factor", "EFECTIVR"), "periodo": limpios.get("periodo")}
        try:
            datos = self._puerta.obtener(f"/xai/{rbd}/shapley", consulta)
        except ErrorDelServicio as exc:
            return ResultadoHerramienta.fallida(self.nombre, str(exc))
        return ResultadoHerramienta.desde(self.nombre, datos, origen="API del servicio SNED")


class SimulacionDeEscenario(_HerramientaConGateway):
    """Estimacion del indice bajo un conjunto de variables de gestion movidas."""

    nombre = "simulacion_de_escenario"
    descripcion = (
        "Estima que Indice SNED resultaria si el establecimiento moviera una o mas variables de "
        "gestion a los valores indicados. Las variables no enviadas conservan su valor observado. "
        "Usela para responder cuanto rinde mover una palanca."
    )
    disparadores = (
        "simula", "simular", "escenario", "que pasaria", "si subo", "si bajo",
        "cuanto rinde", "mover", "aumentar", "subir", "mejorar", "hipotesis",
    )

    def esquema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rbd": {"type": "string"},
                "variables": {
                    "type": "object",
                    "description": "Mapa variable -> valor. Solo variables de gestion.",
                    "additionalProperties": {"type": "number"},
                },
                "periodo": {"type": "string"},
            },
            "required": ["rbd", "variables"],
        }

    def ejecutar(self, **parametros: Any) -> ResultadoHerramienta:
        limpios = self._sanitizador.limpiar(self.nombre, parametros)
        rbd = limpios["rbd"]
        cuerpo = {"periodo": limpios.get("periodo"), "variables": limpios.get("variables", {})}
        if not cuerpo["variables"]:
            return ResultadoHerramienta.fallida(
                self.nombre, "No se indicaron variables de gestion para el escenario."
            )
        try:
            datos = self._puerta.enviar(f"/prediccion/{rbd}/escenario", cuerpo)
        except ErrorDelServicio as exc:
            return ResultadoHerramienta.fallida(self.nombre, str(exc))
        return ResultadoHerramienta.desde(
            self.nombre, {"escenario": cuerpo["variables"], "resultado": datos},
            origen="API del servicio SNED",
        )


def construir_catalogo(
    puerta: PuertaDeServicio, sanitizador: SanitizadorDeParametros | None = None
) -> dict[str, Herramienta]:
    """Registro explicito de herramientas. No hay descubrimiento automatico."""
    san = sanitizador or SanitizadorDeParametros()
    herramientas: list[Herramienta] = [
        DiagnosticoDeEstablecimiento(puerta, san),
        ExplicacionPorFactor(puerta, san),
        SimulacionDeEscenario(puerta, san),
    ]
    return {h.nombre: h for h in herramientas}
