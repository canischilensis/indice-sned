"""Adaptador determinista: rutea y redacta sin red y sin credenciales.

No es un modelo de lenguaje. Es la implementacion de referencia del puerto, y
cumple tres funciones que un proveedor externo no puede cumplir:

  1. Permite que la suite de pruebas y el arnes de evaluacion se ejecuten en
     cualquier maquina, sin clave y sin salida a internet.
  2. Fija el comportamiento esperado del bucle: que herramienta corresponde a
     que intencion, y que debe responder el agente cuando la politica prohibe
     contestar.
  3. Da una linea base contra la cual medir a un proveedor real: si el modelo
     externo rutea peor que un puñado de reglas, el modelo no aporta.

Toda cifra que redacta proviene de la respuesta de la herramienta. Por eso pasa
G-02 por construccion, y por eso G-02 sigue siendo una prueba util: detecta las
regresiones que introduzca cualquier otro proveedor.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from q5_agente.proveedores.contrato import (
    Mensaje,
    PeticionDeHerramienta,
    ProveedorDeModelo,
    RespuestaDelModelo,
)

_RBD_EN_TEXTO = re.compile(r"\bRBD:\s*(\d{1,6})\b")
_PERIODO_EN_TEXTO = re.compile(r"\bPERIODO:\s*(\d{4}-\d{4})\b")

_PIDE_GARANTIA = (
    "garantiza", "garantia", "asegurame", "asegurar el 100", "me aseguras",
    "prometeme", "promesa", "seguro que gano", "voy a ganar", "tendre el 100",
    "obtendre el beneficio", "certeza de obtener",
)
_PIDE_SALTARSE_REGLAS = (
    "ignora", "olvida las instrucciones", "olvida tus reglas", "sin restricciones",
    "modo desarrollador", "cambia los pesos", "modifica la ponderacion",
    "cambiar la ponderacion", "altera la formula", "modifica la formula",
)
_FUERA_DE_ALCANCE = (
    "mejor escuela del pais", "mejor colegio del pais", "ranking nacional completo",
    "que metodologia pedagogica", "recomienda una metodologia", "sugerencia pedagogica",
    "que debo ensenar",
)

#: Como nombra un directivo cada factor. Deliberadamente NO hay codigos aqui.
#:
#: Los codigos vivian escritos en este modulo y se desincronizaron del catalogo:
#: cuatro de los seis quedaron mal escritos y el ruteo pedia factores que el
#: servicio rechazaba. La copia se retiro. El codigo se resuelve contra el enum
#: que declara el esquema de la herramienta, que es la unica fuente del cuanto 5
#: y que a su vez se verifica contra el motor en cada corrida de la suite.
_TERMINOS_DE_FACTOR = (
    "superac", "igualdad", "iniciativ", "integrac", "mejoram", "efectiv",
)

_LEYENDA = (
    "El beneficio se asigna por posicion relativa dentro del Grupo Homogeneo, de modo que "
    "ninguna mejora asegura el cambio de tramo. La inteligencia artificial asiste; la decision "
    "pedagogica y financiera la toma el equipo directivo."
)


def _plano(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def _coma(valor: float, decimales: int = 2) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def _codigos_admitidos(
    herramientas: list[dict[str, Any]], nombre: str, parametro: str
) -> tuple[str, ...]:
    """Valores que el esquema de una herramienta declara para un parametro.

    El adaptador lee el mismo esquema que recibiria un modelo de lenguaje. Esa
    simetria no es estetica: si la linea base rutea con una tabla propia y el
    proveedor externo rutea con el esquema, dejan de ser comparables y la
    comparacion entre ambos —que es lo que la linea base existe para permitir—
    mide dos cosas distintas.
    """
    for herramienta in herramientas:
        if herramienta.get("nombre") != nombre:
            continue
        propiedades = herramienta.get("esquema", {}).get("properties", {})
        admitidos = propiedades.get(parametro, {}).get("enum", ())
        return tuple(str(valor) for valor in admitidos)
    return ()


class AdaptadorDeterminista(ProveedorDeModelo):
    """Ruteo por pertinencia y redaccion por plantilla sobre datos reales."""

    nombre = "determinista"

    def __init__(self, catalogo_disparadores: dict[str, tuple[str, ...]] | None = None) -> None:
        self._disparadores = catalogo_disparadores or {}

    # --- puerto -----------------------------------------------------------

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        consulta = next((m.contenido for m in reversed(mensajes) if m.rol == "usuario"), "")
        observacion = next(
            (m.contenido for m in reversed(mensajes) if m.rol == "herramienta"), None
        )
        entrada = sum(len(m.contenido) for m in mensajes) // 4  # aproximacion

        if observacion is not None:
            texto = self._redactar(observacion, consulta)
            return RespuestaDelModelo(
                texto=texto, tokens_entrada=entrada, tokens_salida=len(texto) // 4
            )

        rechazo = self._politica(consulta)
        if rechazo is not None:
            return RespuestaDelModelo(
                texto=rechazo, tokens_entrada=entrada, tokens_salida=len(rechazo) // 4
            )

        peticion = self._elegir(consulta, herramientas)
        return RespuestaDelModelo(peticion=peticion, tokens_entrada=entrada, tokens_salida=12)

    # --- politica ---------------------------------------------------------

    @staticmethod
    def _politica(consulta: str) -> str | None:
        texto = _plano(consulta)
        if any(f in texto for f in _PIDE_SALTARSE_REGLAS):
            return (
                "No puedo modificar la logica de calculo ni apartarme de las reglas del sistema. "
                "Las ponderaciones de los seis factores son un dato de catalogo fijado por norma y "
                "el agente no las altera: solo consulta lo que el servicio calcula. " + _LEYENDA
            )
        if any(f in texto for f in _PIDE_GARANTIA):
            return (
                "No puedo comprometer la obtencion del beneficio. " + _LEYENDA + " Lo que si puedo "
                "hacer es estimar el indice bajo un escenario concreto y mostrar que variables "
                "aportan mas, con las cifras que devuelve el servicio."
            )
        if any(f in texto for f in _FUERA_DE_ALCANCE):
            return (
                "Esa pregunta queda fuera del alcance del sistema. El agente responde sobre los "
                "establecimientos bajo la jurisdiccion del usuario y sobre las variables que el "
                "indice mide; no emite juicios pedagogicos ni ordena establecimientos ajenos. "
                + _LEYENDA
            )
        return None

    # --- ruteo ------------------------------------------------------------

    def _elegir(self, consulta: str, herramientas: list[dict[str, Any]]) -> PeticionDeHerramienta:
        texto = _plano(consulta)
        mejor, puntaje_mejor = None, -1
        for herramienta in herramientas:
            disparadores = self._disparadores.get(herramienta["nombre"], ())
            puntaje = sum(1 for palabra in disparadores if _plano(palabra) in texto)
            if puntaje > puntaje_mejor:
                mejor, puntaje_mejor = herramienta["nombre"], puntaje
        nombre = mejor or "diagnostico_de_establecimiento"
        if puntaje_mejor <= 0:
            nombre = "diagnostico_de_establecimiento"

        parametros: dict[str, Any] = {}
        rbd = _RBD_EN_TEXTO.search(consulta)
        if rbd:
            parametros["rbd"] = rbd.group(1)
        periodo = _PERIODO_EN_TEXTO.search(consulta)
        if periodo:
            parametros["periodo"] = periodo.group(1)
        if nombre == "explicacion_por_factor":
            factor = self._factor(texto, _codigos_admitidos(herramientas, nombre, "factor"))
            if factor is not None:
                parametros["factor"] = factor
        if nombre == "simulacion_de_escenario":
            parametros["variables"] = self._variables(consulta)
        return PeticionDeHerramienta(nombre=nombre, parametros=parametros)

    @staticmethod
    def _factor(texto: str, codigos: tuple[str, ...]) -> str | None:
        """Elige un codigo de factor entre los que el esquema declara admitidos.

        Aqui no hay codigos escritos a mano. Hay terminos en castellano —lo que
        un directivo dice— y cada termino se resuelve contra el enum de la
        herramienta comparando la raiz del propio codigo: EFECTIVR sin la R
        final es la raiz de "efectividad", SUPERAR la de "superacion".

        Sin coincidencia devuelve el primer codigo admitido, que es el
        comportamiento historico. Que esa eleccion silenciosa sea aceptable esta
        pendiente de decision: hoy una consulta sobre un factor no reconocido
        termina respondida sobre otro sin aviso. Declarado, no corregido.
        """
        for termino in _TERMINOS_DE_FACTOR:
            if termino not in texto:
                continue
            for codigo in codigos:
                if termino.startswith(codigo.removesuffix("R").lower()):
                    return codigo
        return codigos[0] if codigos else None

    @staticmethod
    def _variables(consulta: str) -> dict[str, float]:
        """Lee el bloque VARIABLES: nombre=valor; nombre=valor del mensaje."""
        bloque = re.search(r"VARIABLES:\s*([^\n]+)", consulta)
        if not bloque:
            return {}
        variables: dict[str, float] = {}
        for parte in bloque.group(1).split(";"):
            if "=" not in parte:
                continue
            nombre, valor = parte.split("=", 1)
            try:
                variables[nombre.strip()] = float(valor.strip().replace(",", "."))
            except ValueError:
                continue
        return variables

    # --- redaccion --------------------------------------------------------

    def _redactar(self, observacion: str, consulta: str) -> str:
        try:
            carga = json.loads(observacion)
        except json.JSONDecodeError:
            return "No pude interpretar la respuesta del servicio. " + _LEYENDA

        if not carga.get("exito", True):
            return self._redactar_fallo(carga.get("error", ""))

        datos = carga.get("datos", {})
        herramienta = carga.get("herramienta", "")
        if herramienta == "diagnostico_de_establecimiento":
            return self._redactar_diagnostico(datos)
        if herramienta == "explicacion_por_factor":
            return self._redactar_explicacion(datos)
        if herramienta == "simulacion_de_escenario":
            return self._redactar_escenario(datos)
        return "No dispongo de una lectura para esa herramienta. " + _LEYENDA

    @staticmethod
    def _redactar_fallo(error: str) -> str:
        return (
            "El servicio no entrego datos para esa consulta y por lo tanto no puedo responder con "
            f"cifras. Motivo informado: {error} " + _LEYENDA
        )

    def _redactar_diagnostico(self, datos: dict) -> str:
        prediccion = datos.get("prediccion", {})
        factores = prediccion.get("factores", []) or []
        partes = [
            f"El establecimiento tiene un Indice SNED estimado de "
            f"{_coma(float(prediccion.get('indice', 0)))} puntos"
        ]
        mae = prediccion.get("incertidumbre_mae")
        if mae:
            partes[0] += f", con un error medio de mas o menos {_coma(float(mae))} puntos"
        partes[0] += "."

        if factores:
            ordenados = sorted(
                factores, key=lambda f: abs(f.get("aporte_al_indice", 0)), reverse=True
            )
            mayor = ordenados[0]
            partes.append(
                f"El factor que mas aporta es {mayor.get('nombre', mayor.get('codigo'))}, con "
                f"{_coma(float(mayor.get('aporte_al_indice', 0)))} puntos de aporte sobre una "
                f"ponderacion de {_coma(float(mayor.get('peso', 0)) * 100, 0)} por ciento."
            )
            acotados = [f for f in factores if f.get("es_acotado")]  # frontera declarada
            if acotados:
                partes.append(
                    f"De los {len(factores)} factores, {len(acotados)} estan acotados por "
                    "informacion que el Estado no publica, de modo que su estimacion se interpreta "
                    "dentro de ese limite."
                )

        posicion = datos.get("posicion")
        if posicion:
            partes.append(
                f"Dentro de su Grupo Homogeneo ocupa la posicion "
                f"{posicion.get('posicion_en_grupo')} de {posicion.get('n_grupo')}, "
                f"en el percentil {_coma(float(posicion.get('percentil', 0)))}."
            )

        alertas = datos.get("alertas", []) or []
        if alertas:
            titulos = "; ".join(a.get("titulo", "") for a in alertas[:3])
            partes.append(f"Alertas vigentes: {titulos}.")
        else:
            partes.append("No hay alertas tempranas vigentes.")

        partes.append(_LEYENDA)
        return " ".join(partes)

    def _redactar_explicacion(self, datos: dict) -> str:
        contribuciones = datos.get("contribuciones", []) or []
        # El nombre si el servicio lo entrega; el codigo si no. Un directivo lee
        # "Superacion", no "SUPERAR": el codigo es identificador, no lenguaje.
        # Es el mismo criterio que ya aplicaba la redaccion del diagnostico.
        factor = datos.get("nombre") or datos.get("factor")
        cabeza = (
            f"En el factor {factor} la estimacion es "
            f"{_coma(float(datos.get('prediccion', 0)))} sobre un valor base de "
            f"{_coma(float(datos.get('valor_base', 0)))}."
        )
        if contribuciones:
            mayores = sorted(
                contribuciones, key=lambda c: abs(c.get("contribucion", 0)), reverse=True
            )[:3]
            detalle = "; ".join(
                f"{c.get('etiqueta', c.get('variable'))} aporta "
                f"{_coma(float(c.get('contribucion', 0)))}"
                for c in mayores
            )
            cuerpo = f"Las contribuciones de mayor magnitud son: {detalle}."
        else:
            cuerpo = "El servicio no devolvio contribuciones para este factor."

        # Una variable sin valor observado —`valor: null` en el contrato de la
        # ruta— no es un cero: es una medicion que el establecimiento no tiene.
        # Se nombra siempre, aunque su contribucion no entre entre las tres
        # mayores, porque descartar una ausencia por pequeña es precisamente
        # tratarla como cero, que es lo que este sistema existe para no hacer.
        ausentes = [c for c in contribuciones if c.get("valor") is None]
        if ausentes:
            faltantes = "; ".join(
                f"{c.get('etiqueta', c.get('variable'))} aporta "
                f"{_coma(float(c.get('contribucion', 0)))}"
                for c in ausentes
            )
            aviso = (
                "Hay mediciones que este establecimiento no tiene y su ausencia no se trata como "
                f"un cero: {faltantes}. Esa cifra es el efecto de la falta del dato, no el de un "
                "valor bajo."
            )
        else:
            aviso = ""

        aditividad = (
            "La aditividad quedo verificada, de modo que la descomposicion reproduce la prediccion."
            if datos.get("aditividad_verificada")
            else "La aditividad NO quedo verificada: la descomposicion debe leerse con reserva."
        )
        partes = [cabeza, cuerpo, aviso, aditividad, _LEYENDA]
        return " ".join(p for p in partes if p)

    def _redactar_escenario(self, datos: dict) -> str:
        resultado = datos.get("resultado", {})
        movidas = datos.get("escenario", {}) or {}
        listado = "; ".join(f"{k} = {_coma(float(v))}" for k, v in movidas.items())
        cabeza = (
            f"Bajo el escenario indicado ({listado}), el indice estimado es "
            f"{_coma(float(resultado.get('indice', 0)))} puntos."
        )
        mae = resultado.get("incertidumbre_mae")
        margen = (
            f" El error medio del motor es de mas o menos {_coma(float(mae))} puntos, "
            "de modo que diferencias menores a ese margen no son distinguibles."
            if mae
            else ""
        )
        return cabeza + margen + " " + _LEYENDA
