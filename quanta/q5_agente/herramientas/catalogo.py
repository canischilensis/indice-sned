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

#: Los seis codigos de factor, tal como los nombra el motor predictivo.
#:
#: Estan duplicados aqui a proposito: la frontera de cuantos prohibe que el
#: cuanto 5 importe q2_modelamiento, y esa prohibicion es lo que permite
#: retirarlo sin tocar el resto. El precio de la duplicacion es que puede
#: desincronizarse, y se desincronizo: cuatro de los seis codigos estaban mal
#: escritos —SUPERACR, INICIATR, MEJORAMR, IGUALDAR— y el modelo, obediente,
#: pedia con ellos hasta que el servicio los rechazaba.
#:
#: `tests/integracion/q5/test_codigos_de_factor.py` compara esta tupla contra
#: COLUMNAS_OBJETIVO del cuanto 2 en cada ejecucion de la suite. La prueba puede
#: cruzar la frontera porque no forma parte del cuanto: es su verificacion.
FACTORES = ("EFECTIVR", "SUPERAR", "INICIAR", "MEJORAR", "INTEGRAR", "IGUALDR")


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


class ConsultaDeDoctrina(Herramienta):
    """Responde sobre las decisiones del proyecto, no sobre el establecimiento.

    Es la unica herramienta que no habla con el servicio. Lee la documentacion
    versionada y devuelve el fragmento pertinente con su procedencia.

    **Sus cifras salen por un conjunto aparte.** Una magnitud leida de un
    documento no es una medicion: fue cierta cuando se escribio y pudo dejar de
    serlo. G-02 la acepta solo si el texto nombra el documento del que sale.
    """

    nombre = "consulta_de_doctrina"
    descripcion = (
        "Consulta la documentacion versionada del proyecto —decisiones de arquitectura, "
        "manuales, planes— para responder por que el sistema es como es. No devuelve datos "
        "del establecimiento: para eso estan las otras herramientas. Toda cifra que entregue "
        "debe citarse nombrando el documento del que proviene."
    )
    disparadores = (
        "por que el sistema", "que decidieron", "decision", "adr", "doctrina",
        "documentacion", "esta documentado", "por que se descarto", "criterio",
        "por que es acotado", "que dice el manual", "metodologia",
    )

    def __init__(self, recuperador: Any, maximo: int = 3) -> None:
        self._recuperador = recuperador
        self._maximo = maximo

    def esquema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"consulta": {"type": "string"}},
            "required": ["consulta"],
        }

    def ejecutar(self, **parametros: Any) -> ResultadoHerramienta:
        consulta = str(parametros.get("consulta") or "").strip()
        if not consulta:
            return ResultadoHerramienta.fallida(self.nombre, "Falta el texto de la consulta.")

        fragmentos = self._recuperador.recuperar(consulta, self._maximo)
        if not fragmentos:
            return ResultadoHerramienta.fallida(
                self.nombre, "La documentacion del proyecto no cubre esa consulta."
            )

        procedencias = [p for f in fragmentos for p in f.procedencias()]
        datos = {
            "consulta": consulta,
            "fragmentos": [
                {
                    "documento": f.documento,
                    "ancla": f.ancla,
                    "texto": f.texto,
                    "huella": f.huella,
                }
                for f in fragmentos
            ],
        }
        return ResultadoHerramienta.desde_documentos(self.nombre, datos, procedencias)


def construir_catalogo(
    puerta: PuertaDeServicio,
    sanitizador: SanitizadorDeParametros | None = None,
    recuperador: Any | None = None,
) -> dict[str, Herramienta]:
    """Registro explicito de herramientas. No hay descubrimiento automatico.

    La herramienta de doctrina entra **solo si se le entrega un recuperador**.
    Agregar una herramienta cambia el ruteo, y los veinte casos criticos y la
    comparacion entre orquestadores quedarian medidos contra otro catalogo sin
    que nadie lo hubiera decidido. Se enciende por configuracion, cuando se vaya
    a medir el efecto a proposito.
    """
    san = sanitizador or SanitizadorDeParametros()
    herramientas: list[Herramienta] = [
        DiagnosticoDeEstablecimiento(puerta, san),
        ExplicacionPorFactor(puerta, san),
        SimulacionDeEscenario(puerta, san),
    ]
    if recuperador is not None:
        herramientas.append(ConsultaDeDoctrina(recuperador))
    return {h.nombre: h for h in herramientas}
