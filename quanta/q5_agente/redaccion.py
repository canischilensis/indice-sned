"""Normalizacion del texto final del agente a prosa plana en castellano.

El contrato del puerto `AsesorDeGestion` dice que `texto` es prosa: la interfaz
la pinta tal cual, sin interpretar marcas. El adaptador determinista lo cumple
por construccion. Un proveedor externo no: responde en Markdown por costumbre, y
en la ventana se leen los asteriscos.

Se le pide en el mensaje de sistema que no lo haga. Eso no basta y no debe
bastar: una instruccion a un modelo es una peticion, no una garantia. Es el
mismo criterio de G-02, donde no se le pide al modelo que cite bien sino que se
verifica que lo haya hecho. Aqui la garantia la da esta funcion, en el bucle,
para cualquier proveedor presente o futuro.

Dos transformaciones:

1. **Marcas de Markdown.** Se retiran enfasis, encabezados, reglas, vinetas,
   codigo y enlaces. No se convierten a HTML en ningun punto: transformar la
   salida de un modelo en marcado ejecutable por el navegador es una puerta que
   este sistema no necesita abrir por un problema de negritas.

2. **Separador decimal.** Hacia el usuario, coma; internamente, punto. Los datos
   viajan y se comparan en punto —es lo que devuelve el servicio y lo que lee el
   guardarrail— y solo el texto que se muestra usa la convencion chilena.

Limitacion declarada: solo se convierten decimales de una o dos cifras. Tres
digitos despues de un punto son indistinguibles de un grupo de millar en
castellano (`4.435` son cuatro mil), y equivocarse en ese sentido corrompe una
cantidad. Un numero con tres o mas decimales conserva el punto.
"""

from __future__ import annotations

import re

#: Linea compuesta solo por tres o mas guiones, asteriscos o guiones bajos.
_REGLA_HORIZONTAL = re.compile(r"^[ \t]*([-*_])\1{2,}[ \t]*$", re.MULTILINE)

#: Encabezados ATX. Se retira la marca y se conserva el texto como una frase.
_ENCABEZADO = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]*", re.MULTILINE)

#: Vineta al principio de linea. Se conserva la sangria, que transmite jerarquia.
_VINETA = re.compile(r"^([ \t]*)[-*+][ \t]+", re.MULTILINE)

_FUERTE = re.compile(r"\*\*(\S(?:.*?\S)?)\*\*", re.DOTALL)
_FUERTE_BAJO = re.compile(r"__(\S(?:.*?\S)?)__", re.DOTALL)

#: Enfasis simple con asterisco. El guion bajo suelto NO se toca a proposito:
#: los nombres de variable del dominio lo llevan —`tasa_aprobacion`,
#: `falta_simce_2m`— y tratarlos como marcado los destruiria.
_ENFASIS = re.compile(r"(?<![\w*])\*(\S(?:[^*\n]*\S)?)\*(?![\w*])")

_CODIGO = re.compile(r"`([^`\n]+)`")
_ENLACE = re.compile(r"\[([^\]\n]+)\]\([^)\s]+\)")

#: Punto decimal con una o dos cifras.
#:
#: - `(?<!\.\d)` descarta el segundo punto de una version tipo 1.0.0, donde el
#:   grupo anterior ya venia precedido de punto.
#: - `(?!\d)` descarta los grupos de millar: en `4.435` el grupo tiene tres.
#: - `(?!\.\d)` descarta el primer punto de esa misma version, sin romper el
#:   punto final de una frase que termina en cifra.
_DECIMAL = re.compile(r"(?<!\.\d)(?<=\d)\.(\d{1,2})(?!\d)(?!\.\d)")

_LINEAS_EN_BLANCO = re.compile(r"\n{3,}")
_ESPACIOS_AL_FINAL = re.compile(r"[ \t]+$", re.MULTILINE)


def sin_markdown(texto: str) -> str:
    """Retira las marcas de Markdown conservando el contenido y la jerarquia."""
    limpio = _ENLACE.sub(r"\1", texto)
    limpio = _CODIGO.sub(r"\1", limpio)
    limpio = _REGLA_HORIZONTAL.sub("", limpio)
    limpio = _ENCABEZADO.sub("", limpio)
    limpio = _VINETA.sub(r"\1· ", limpio)
    limpio = _FUERTE.sub(r"\1", limpio)
    limpio = _FUERTE_BAJO.sub(r"\1", limpio)
    limpio = _ENFASIS.sub(r"\1", limpio)
    return limpio


def con_coma_decimal(texto: str) -> str:
    """Convierte el separador decimal a coma, que es la convencion chilena."""
    return _DECIMAL.sub(r",\1", texto)


def a_prosa_plana(texto: str) -> str:
    """Deja el texto como lo exige el contrato: prosa, sin marcado, con coma.

    Se aplica ANTES de evaluar la politica de salida, no despues. El guardarrail
    debe juzgar exactamente lo que el usuario va a leer; validar una version y
    entregar otra deja un hueco por donde no mira nadie.
    """
    limpio = con_coma_decimal(sin_markdown(texto))
    limpio = _ESPACIOS_AL_FINAL.sub("", limpio)
    limpio = _LINEAS_EN_BLANCO.sub("\n\n", limpio)
    return limpio.strip()
