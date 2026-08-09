"""Guardarrailes del cuanto 5.

Tres barreras, en orden de aplicacion:

  G-01  Sanitizacion de parametros. Una herramienta jamas recibe un valor que no
        haya pasado por aqui. Cierra la inyeccion por parametro.
  G-02  Fundamentacion de cifras. Toda magnitud citada en el texto debe existir
        en alguna respuesta de herramienta. Cierra la alucinacion de cifras.
  G-03  Prohibicion de promesas de retorno. El beneficio se asigna por posicion
        relativa dentro del Grupo Homogeneo: ninguna mejora lo garantiza.

Las tres se expresan como Especificacion, el mismo puerto que gobierna las
reglas de cuarentena de la ingesta y las reglas de alerta del servicio. No es
ornamento: permite componerlas con Y / O / NO y darle a cada una su prueba.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field

from compartido.especificacion import Especificacion

from q5_agente.errores import ParametroInvalido

# --- G-01 · sanitizacion ----------------------------------------------------

_RBD = re.compile(r"^\d{1,6}$")
_PERIODO = re.compile(r"^\d{4}-\d{4}$")
_NOMBRE_VARIABLE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")

#: Variables de gestion admisibles en un escenario. Deliberadamente cerrada:
#: el agente no puede inventar nombres de columnas ni tocar el objetivo.
VARIABLES_DE_GESTION = frozenset({
    "simce_mat_4b", "simce_leng_4b", "simce_mat_2m", "simce_leng_2m",
    "tasa_aprobacion", "tasa_retiro", "tasa_asistencia",
    "idps_clima", "idps_autoestima", "idps_participacion", "idps_habitos",
    "dotacion_docente", "matricula_total",
})

#: Nunca pueden entrar como parametro: son el objetivo o la agrupacion.
VARIABLES_PROHIBIDAS = frozenset({
    "indicer", "sel", "cluster_codigo", "efectivr", "superacr",
    "iniciatr", "mejoramr", "igualdar", "integrar",
})


def _a_flotante(valor: object) -> float | None:
    """Acepta el numero, o su escritura en castellano con coma decimal."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        texto = valor.strip().replace(" ", "")
        if texto.count(",") == 1 and texto.count(".") == 0:
            texto = texto.replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return None
    return None


class SanitizadorDeParametros:
    """G-01. Valida forma y dominio antes de tocar el servicio."""

    codigo = "G-01"

    def __init__(
        self,
        variables_permitidas: frozenset[str] = VARIABLES_DE_GESTION,
        maximo_variables: int = 8,
    ) -> None:
        self._permitidas = variables_permitidas
        self._maximo = maximo_variables

    def limpiar(self, herramienta: str, parametros: dict) -> dict:
        rbd = str(parametros.get("rbd", "")).strip()
        if not _RBD.match(rbd):
            raise ParametroInvalido(
                f"El RBD '{rbd}' no tiene forma valida: se esperan entre 1 y 6 digitos."
            )
        limpio: dict = {"rbd": rbd}

        periodo = parametros.get("periodo")
        if periodo not in (None, "", "null"):
            periodo = str(periodo).strip()
            if not _PERIODO.match(periodo):
                raise ParametroInvalido(
                    f"El periodo '{periodo}' no tiene forma valida: se espera 'AAAA-AAAA'."
                )
            limpio["periodo"] = periodo

        factor = parametros.get("factor")
        if factor:
            factor = str(factor).strip().upper()
            if not factor.isalpha() or len(factor) > 12:
                raise ParametroInvalido(f"El factor '{factor}' no tiene forma valida.")
            limpio["factor"] = factor

        variables = parametros.get("variables")
        if variables is not None:
            if not isinstance(variables, dict):
                raise ParametroInvalido("El campo 'variables' debe ser un mapa nombre -> valor.")
            if len(variables) > self._maximo:
                raise ParametroInvalido(
                    f"Un escenario admite a lo mas {self._maximo} variables; llegaron "
                    f"{len(variables)}."
                )
            limpio["variables"] = {
                k: v for k, v in (self._variable(k, v) for k, v in variables.items())
            }
        return limpio

    def _variable(self, nombre: str, valor: object) -> tuple[str, float]:
        clave = str(nombre).strip().lower()
        if not _NOMBRE_VARIABLE.match(clave):
            raise ParametroInvalido(f"El nombre de variable '{nombre}' no es admisible.")
        if clave in VARIABLES_PROHIBIDAS:
            raise ParametroInvalido(
                f"La variable '{clave}' es objetivo o agrupacion del indice y no puede moverse."
            )
        if clave not in self._permitidas:
            raise ParametroInvalido(
                f"La variable '{clave}' no esta en el catalogo de variables de gestion."
            )
        numero = _a_flotante(valor)
        if numero is None:
            raise ParametroInvalido(f"El valor de '{clave}' no es numerico.")
        if not math.isfinite(numero):
            raise ParametroInvalido(f"El valor de '{clave}' no es finito.")
        return clave, numero


# --- G-02 · fundamentacion de cifras ---------------------------------------

#: Numeros con parte decimal, porcentajes o enteros de dos digitos o mas. Los
#: enteros de un digito quedan fuera a proposito: no pueden ser un indice ni un
#: puntaje, y excluirlos evita rechazar enumeraciones ("los tres factores").
_MAGNITUD = re.compile(
    r"(?<![\w.,])("
    r"\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?"   # miles con punto o espacio: 44.679
    r"|\d+,\d+"                            # decimal en castellano: 67,60
    r"|\d+\.\d+"                           # decimal con punto: 2.31
    r"|\d+"                                 # entero suelto
    r")(?![\w])"
)


def _a_numero(bruto: str) -> float | None:
    texto = bruto.replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def extraer_magnitudes(texto: str) -> list[float]:
    """Devuelve las magnitudes citadas en el texto, normalizadas a punto decimal."""
    encontradas: list[float] = []
    for bruto in _MAGNITUD.findall(texto):
        numero = _a_numero(bruto)
        if numero is None:
            continue
        if numero.is_integer() and abs(numero) < 10:
            continue
        encontradas.append(numero)
    return encontradas


@dataclass
class Fundamentacion:
    """Candidato que evalua G-03 y G-02: el texto junto a su evidencia."""

    texto: str
    cifras_disponibles: set[float] = field(default_factory=set)


class CifrasFundadasEnHerramientas(Especificacion[Fundamentacion]):
    """G-02. Ninguna magnitud del texto puede faltar en las respuestas obtenidas."""

    codigo = "G-02"
    descripcion = "Toda cifra citada proviene de una respuesta de herramienta."

    def __init__(self, tolerancia: float = 0.011) -> None:
        self._tolerancia = tolerancia

    def cifras_sin_respaldo(self, candidato: Fundamentacion) -> list[float]:
        huerfanas: list[float] = []
        for citada in extraer_magnitudes(candidato.texto):
            if not self._respaldada(citada, candidato.cifras_disponibles):
                huerfanas.append(citada)
        return huerfanas

    def _respaldada(self, citada: float, disponibles: set[float]) -> bool:
        for bruto in disponibles:
            # El signo viaja en la prosa ("resta 1,20"), no en la magnitud extraida.
            for real in (bruto, abs(bruto)):
                if abs(real - citada) <= self._tolerancia:
                    return True
                # El texto puede redondear: 67,6 respalda a 67,60 y viceversa.
                if round(real, 1) == round(citada, 1) and abs(real - citada) < 0.05:
                    return True
                # Una proporcion puede citarse como porcentaje: 0,37 respalda a 37.
                if abs(real * 100 - citada) <= self._tolerancia:
                    return True
        return False

    def es_satisfecha_por(self, candidato: Fundamentacion) -> bool:
        return not self.cifras_sin_respaldo(candidato)


# --- G-03 · prohibicion de promesas de retorno ------------------------------

#: Raices, no formas conjugadas: "garantiz" cubre garantizo, garantiza y
#: garantizado. Una promesa escrita en primera persona es igual de invalida.
_PROMESAS = (
    "garantiz", "asegura la excelencia", "aseguramos la excelencia",
    "con certeza obtendra", "obtendra el beneficio", "obtendran el beneficio",
    "tendra el 100", "asegurara el sned", "le aseguro", "les aseguro",
    "sin duda ganara", "va a ganar el sned", "ganara el sned",
    "conseguira la subvencion", "conseguiran la subvencion",
)


def _sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


class SinPromesasDeRetorno(Especificacion[Fundamentacion]):
    """G-03. El beneficio se asigna por posicion relativa: nada lo garantiza."""

    codigo = "G-03"
    descripcion = "El texto no promete la obtencion del beneficio."

    def frases_detectadas(self, candidato: Fundamentacion) -> list[str]:
        plano = _sin_tildes(candidato.texto)
        return [frase for frase in _PROMESAS if frase in plano]

    def es_satisfecha_por(self, candidato: Fundamentacion) -> bool:
        return not self.frases_detectadas(candidato)


# --- composicion ------------------------------------------------------------


class PoliticaDeSalida:
    """Aplica G-02 y G-03 sobre el texto generado y explica por que rechaza."""

    def __init__(self, fundamentacion: bool = True, promesas: bool = True) -> None:
        self.cifras = CifrasFundadasEnHerramientas()
        self.promesas = SinPromesasDeRetorno()
        self._usar_cifras = fundamentacion
        self._usar_promesas = promesas

    @property
    def especificacion(self) -> Especificacion[Fundamentacion]:
        reglas: list[Especificacion[Fundamentacion]] = []
        if self._usar_cifras:
            reglas.append(self.cifras)
        if self._usar_promesas:
            reglas.append(self.promesas)
        if not reglas:
            raise ValueError("La politica de salida necesita al menos una regla activa.")
        combinada = reglas[0]
        for regla in reglas[1:]:
            combinada = combinada.y(regla)
        return combinada

    def evaluar(self, texto: str, cifras: set[float]) -> tuple[bool, str | None, str | None]:
        """Devuelve (aceptado, codigo del guardarrail, motivo)."""
        candidato = Fundamentacion(texto=texto, cifras_disponibles=cifras)
        if self._usar_promesas:
            frases = self.promesas.frases_detectadas(candidato)
            if frases:
                return False, self.promesas.codigo, (
                    "La respuesta prometia la obtencion del beneficio: "
                    + ", ".join(f"'{f}'" for f in frases)
                )
        if self._usar_cifras:
            huerfanas = self.cifras.cifras_sin_respaldo(candidato)
            if huerfanas:
                citadas = ", ".join(f"{c:g}" for c in huerfanas[:5])
                return False, self.cifras.codigo, (
                    f"La respuesta citaba cifras que ninguna herramienta devolvio: {citadas}"
                )
        return True, None, None
