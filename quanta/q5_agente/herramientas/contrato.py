"""Puerto Herramienta y el resultado que toda herramienta debe devolver.

Cada herramienta envuelve rutas que ya existen y estan probadas. El agente no
calcula: pide. El resultado transporta, ademas de los datos, el conjunto de
cifras que el servicio devolvio, porque ese conjunto es lo que el guardarrail de
fundamentacion usara para aceptar o rechazar el texto generado.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


def _recolectar_cifras(nodo: Any, acumulado: set[float]) -> None:
    """Recorre la respuesta y acumula toda cifra finita que contenga."""
    if isinstance(nodo, bool):
        return
    if isinstance(nodo, (int, float)):
        if math.isfinite(float(nodo)):
            acumulado.add(round(float(nodo), 6))
        return
    if isinstance(nodo, dict):
        for valor in nodo.values():
            _recolectar_cifras(valor, acumulado)
        return
    if isinstance(nodo, (list, tuple)):
        for valor in nodo:
            _recolectar_cifras(valor, acumulado)


@dataclass(frozen=True)
class Procedencia:
    """De donde sale una cifra que se leyo en un documento.

    Guardar el valor no basta. Una cifra citada de un documento es **evidencia
    mas debil** que una consulta en vivo al motor: el documento pudo escribirse
    en marzo y el sistema haber cambiado en agosto. Para que la auditoria pueda
    distinguirlas hace falta saber de que documento salio, de que parte, y de
    cuando data esa parte.
    """

    valor: float
    #: Tal como esta escrita en el documento, con su separador y su signo.
    literal: str
    #: Ruta relativa a la raiz del repositorio.
    documento: str
    #: Encabezado bajo el que aparece, o la linea si no hay encabezado.
    ancla: str
    #: Fecha del ultimo cambio registrado para esa parte, en formato ISO. Sale
    #: del historial de versiones y no de la fecha del archivo en disco: un
    #: clon reciente pone la fecha de hoy a un texto de marzo.
    fecha: str = ""
    #: Huella corta del fragmento. Permite detectar que el texto cambio aunque
    #: la cifra siga siendo la misma.
    huella: str = ""


@dataclass
class ResultadoHerramienta:
    """Lo que una herramienta entrega al bucle.

    Distingue **tres** conjuntos de cifras, y la distincion es lo que permite
    auditar la respuesta en vez de solo aceptarla:

    - `cifras` son magnitudes del **dato**: el indice, un aporte, un percentil.
      Las calculo el motor durante esta consulta. Es la evidencia mas fuerte.
    - `cifras_diagnostico` son magnitudes que aparecen en un **mensaje del
      sistema**: un RBD dentro de un 403, un puerto dentro de un error de
      conexion. No son una afirmacion sobre el establecimiento, pero tampoco
      son invencion del modelo: repetirlas literalmente es lo correcto.
    - `cifras_documentales` son magnitudes leidas de un **documento del
      proyecto**: el R2 declarado, el numero de tablas, el porcentaje de
      ponderacion acotada. Son verdaderas cuando se escribieron y pueden haber
      dejado de serlo. Viajan con su `Procedencia` para que quien lea la
      respuesta sepa que esta leyendo un archivo y no una medicion.

    Sin el tercer conjunto, una cifra sacada de un documento entraria por la
    puerta del primero y G-02 la trataria como respaldada por el motor. La
    auditoria diria "fundada" sobre algo que solo esta escrito.
    """

    herramienta: str
    datos: dict[str, Any]
    origen: str
    exito: bool = True
    error: str | None = None
    cifras: set[float] = field(default_factory=set)
    cifras_diagnostico: set[float] = field(default_factory=set)
    cifras_documentales: set[float] = field(default_factory=set)
    procedencias: tuple[Procedencia, ...] = ()

    @classmethod
    def desde(cls, herramienta: str, datos: dict[str, Any], origen: str) -> ResultadoHerramienta:
        cifras: set[float] = set()
        _recolectar_cifras(datos, cifras)
        return cls(herramienta=herramienta, datos=datos, origen=origen, cifras=cifras)

    @classmethod
    def desde_documentos(
        cls, herramienta: str, datos: dict[str, Any], procedencias: Sequence[Procedencia]
    ) -> ResultadoHerramienta:
        """Resultado de una consulta a la documentacion del proyecto.

        Las cifras entran por el tercer conjunto, nunca por el primero. Es la
        frontera que sostiene el argumento del capitulo: **las herramientas
        responden sobre el dato, la recuperacion responde sobre la doctrina**, y
        mezclarlas convertiria un archivo en una medicion.
        """
        return cls(
            herramienta=herramienta,
            datos=datos,
            origen="documentacion del proyecto",
            cifras_documentales={p.valor for p in procedencias},
            procedencias=tuple(procedencias),
        )

    @classmethod
    def fallida(cls, herramienta: str, error: str) -> ResultadoHerramienta:
        from q5_agente.guardarrailes import extraer_magnitudes  # noqa: PLC0415

        return cls(
            herramienta=herramienta,
            datos={},
            origen="ninguno",
            exito=False,
            error=error,
            cifras_diagnostico=set(extraer_magnitudes(error)),
        )


class Herramienta(ABC):
    """Puerto: una capacidad que el agente puede invocar sobre el servicio."""

    nombre: str = "sin_nombre"
    descripcion: str = ""
    #: Palabras que, presentes en la consulta, hacen pertinente esta herramienta.
    disparadores: tuple[str, ...] = ()

    @abstractmethod
    def esquema(self) -> dict[str, Any]:
        """Descripcion de parametros, en el formato que los proveedores esperan."""

    @abstractmethod
    def ejecutar(self, **parametros: Any) -> ResultadoHerramienta:
        """Invoca el servicio y devuelve datos verificables."""

    def pertinencia(self, texto: str) -> int:
        """Puntaje de correspondencia con la consulta. Lo usa el ruteo local."""
        minuscula = texto.lower()
        return sum(1 for palabra in self.disparadores if palabra in minuscula)
