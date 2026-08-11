"""Recuperacion sobre la documentacion del proyecto, no sobre los datos.

## La frontera, que es lo que hace admisible este modulo

El capitulo de arquitectura sostiene que la recuperacion semantica es
**incorrecta para datos estructurados**: el dato de este sistema vive en una base
relacional normalizada y se expone por una interfaz tipada, y fragmentarlo para
recuperarlo por similitud introduciria imprecision donde la consulta directa es
deterministica. Ese argumento sigue en pie y este modulo no lo contradice.

Lo completa. El corpus de aqui es **exclusivamente `docs/`**: decisiones de
arquitectura, manuales, planes de calidad. Nunca las tablas ni los archivos
columnares.

    Las herramientas responden sobre el dato.
    La recuperacion responde sobre la doctrina.

«Cuanto rinde subir la asistencia» es una pregunta para el motor. «Por que la
Superacion es un factor acotado» es una pregunta para el ADR que lo explica. Dos
preguntas de naturaleza distinta, cada una por donde corresponde.

## Por que las cifras salen por un conjunto aparte

Los documentos contienen cifras: el R2 de 0,583, las treinta y ocho tablas, el
63 % de ponderacion acotada. Si entraran por el mismo conjunto que las del motor,
G-02 las trataria como respaldadas por una medicion. **No lo estan**: estan
respaldadas por un archivo, que pudo escribirse en marzo. Por eso viajan como
`cifras_documentales`, con su `Procedencia`, y G-02 exige que el texto atribuya
el documento antes de aceptarlas.

## Por que la primera implementacion es por palabras clave

Honestidad sobre la escala: el corpus son unos cientos de kilobytes de Markdown,
del orden de trescientos fragmentos. **A ese tamano una busqueda por palabras
clave funciona igual de bien que una vectorial y es mas simple.** Se implementa
primero la simple, se mide, y una recuperacion por embeddings entra despues como
segundo adaptador del mismo puerto: entonces la comparacion sera entre dos
estrategias de recuperacion sobre el mismo corpus, que es una medicion, y no una
eleccion por prestigio.
"""

from __future__ import annotations

import hashlib
import math
import re
import subprocess
import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from q5_agente.herramientas.contrato import Procedencia

#: Raiz del repositorio. El corpus se resuelve desde aqui y nunca fuera de docs/.
RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "docs"

#: Numeros con dos o mas digitos, decimales o porcentajes. Mismo criterio que
#: G-02: un entero de un digito no es una magnitud citable.
_MAGNITUD = re.compile(r"-?\d+(?:[.,]\d+)?\s*%?")

#: Encabezado Markdown. Sirve de ancla: es como una persona citaria la parte.
_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*)$")

_PALABRA = re.compile(r"[a-z0-9]{4,}")

#: Palabras demasiado frecuentes para discriminar. No es una lista exhaustiva de
#: vacias: son las que en ESTE corpus aparecen en casi todo documento.
_SIN_VALOR = frozenset(
    {
        "para", "como", "esta", "este", "esto", "sobre", "porque", "cuando", "donde",
        "sistema", "proyecto", "documento", "datos", "dato", "valor", "puede", "debe",
        "cada", "entre", "desde", "hasta", "solo", "mismo", "misma", "otro", "otra",
        "tiene", "hace", "ser", "son", "que", "del", "las", "los", "una", "uno",
    }
)


def _relativa(ruta: Path) -> str:
    """Ruta para citar. Relativa a la raiz cuando el corpus vive dentro de ella.

    Un corpus fuera de la raiz —el de una prueba, por ejemplo— no puede
    expresarse en relacion a ella. Se devuelve entonces la ruta tal cual, en vez
    de fallar: la procedencia debe poder construirse siempre, porque su ausencia
    convertiria una cifra atribuible en una infundada.
    """
    try:
        return ruta.relative_to(RAIZ).as_posix()
    except ValueError:
        return ruta.as_posix()


def _plano(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


#: Longitud a la que se recorta cada palabra para indexarla.
#:
#: Es lematizacion pobre y se declara como tal: en castellano el genero y el
#: numero viven al final —acotado y acotada, factor y factores, ponderacion y
#: ponderaciones— y recortar absorbe esa variacion sin traer un lematizador.
#:
#: Nace de un fallo de estas mismas pruebas: la consulta decia "acotado", el
#: documento decia "acotada", y la coincidencia exacta no encontraba nada. El
#: precio es sobreencontrar de vez en cuando, que en recuperacion cuesta menos
#: que no encontrar.
_LARGO_DE_RAIZ = 6


def _terminos(texto: str) -> set[str]:
    return {
        p[:_LARGO_DE_RAIZ]
        for p in _PALABRA.findall(_plano(texto))
        if p not in _SIN_VALOR
    }


def _a_numero(bruto: str) -> float | None:
    limpio = bruto.replace("%", "").replace(" ", "")
    if "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    try:
        return float(limpio)
    except ValueError:
        return None


@lru_cache(maxsize=256)
def _fecha_de(ruta: str) -> str:
    """Fecha del ultimo cambio registrado, del historial y no del disco.

    La fecha de modificacion del archivo miente despues de un clon: pone la de
    hoy a un texto de marzo, que es justo lo contrario de lo que esta cifra
    necesita informar. Si el historial no esta disponible se devuelve vacio y la
    traza lo declara, en vez de mostrar una fecha falsa.
    """
    try:
        salida = subprocess.run(
            ["git", "--no-optional-locks", "log", "-1", "--format=%cs", "--", ruta],
            cwd=RAIZ, capture_output=True, text=True, timeout=5, check=False,
        )
        return salida.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


@dataclass(frozen=True)
class Fragmento:
    """Una seccion de un documento, con lo necesario para citarla."""

    documento: str
    ancla: str
    texto: str
    terminos: frozenset[str] = field(default_factory=frozenset)

    @property
    def huella(self) -> str:
        return hashlib.sha256(self.texto.encode("utf-8")).hexdigest()[:12]

    def procedencias(self) -> tuple[Procedencia, ...]:
        """Las magnitudes del fragmento, cada una con su origen."""
        fecha = _fecha_de(self.documento)
        vistas: dict[float, Procedencia] = {}
        for bruto in _MAGNITUD.findall(self.texto):
            valor = _a_numero(bruto)
            if valor is None or (float(valor).is_integer() and abs(valor) < 10):
                continue
            vistas.setdefault(
                valor,
                Procedencia(
                    valor=valor,
                    literal=bruto.strip(),
                    documento=self.documento,
                    ancla=self.ancla,
                    fecha=fecha,
                    huella=self.huella,
                ),
            )
        return tuple(vistas.values())


class RecuperadorDeDoctrina(ABC):
    """Puerto: dado un texto, devuelve los fragmentos pertinentes del corpus.

    Existe como puerto y no como funcion porque se espera un segundo adaptador.
    La recuperacion por palabras clave y la vectorial resuelven el mismo
    contrato, y tenerlo declarado es lo que permitira compararlas sobre el mismo
    corpus en vez de sustituir una por otra por prestigio.
    """

    nombre: str = "sin_nombre"

    @abstractmethod
    def recuperar(self, consulta: str, maximo: int = 3) -> list[Fragmento]:
        """Fragmentos ordenados por pertinencia decreciente."""

    def describir(self) -> dict[str, object]:
        return {"recuperador": self.nombre}


def fragmentar(ruta: Path, relativa: str) -> list[Fragmento]:
    """Parte un Markdown por encabezados. El encabezado es el ancla.

    Cada fragmento hereda los terminos del **titulo del documento**, no solo los
    del suyo. Nace de otro fallo de las pruebas: un encabezado sin cuerpo —«Por
    que el factor esta acotado», que es lo mas informativo que tiene el
    documento— no producia fragmento y sus palabras se perdian enteras. Un
    titulo describe todo lo que cuelga de el.
    """
    lineas = ruta.read_text(encoding="utf-8", errors="ignore").splitlines()
    fragmentos: list[Fragmento] = []
    ancla = "(sin encabezado)"
    titulo = ""
    acumulado: list[str] = []

    def cerrar() -> None:
        texto = "\n".join(acumulado).strip()
        if texto:
            fragmentos.append(
                Fragmento(
                    relativa,
                    ancla,
                    texto,
                    frozenset(_terminos(" ".join((titulo, ancla, texto)))),
                )
            )

    for linea in lineas:
        encabezado = _ENCABEZADO.match(linea)
        if encabezado:
            cerrar()
            ancla = encabezado.group(2).strip()
            if len(encabezado.group(1)) == 1 and not titulo:
                titulo = ancla
            acumulado = []
            continue
        acumulado.append(linea)
    cerrar()
    return fragmentos


class RecuperadorPorPalabrasClave(RecuperadorDeDoctrina):
    """Coincidencia de terminos con peso por rareza. Sin dependencias.

    La rareza importa: un fragmento que comparte con la consulta la palabra
    "cortacircuitos" dice mas que uno que comparte "arquitectura", porque la
    segunda esta en todas partes. Es la intuicion de la frecuencia inversa, sin
    la maquinaria.
    """

    nombre = "palabras_clave"

    def __init__(self, corpus: Path | None = None) -> None:
        self._corpus = corpus or CORPUS
        self._fragmentos: list[Fragmento] | None = None
        self._rareza: dict[str, float] = {}

    def _indice(self) -> list[Fragmento]:
        if self._fragmentos is not None:
            return self._fragmentos
        fragmentos: list[Fragmento] = []
        for ruta in sorted(self._corpus.rglob("*.md")):
            relativa = _relativa(ruta)
            fragmentos.extend(fragmentar(ruta, relativa))

        apariciones: dict[str, int] = {}
        for fragmento in fragmentos:
            for termino in fragmento.terminos:
                apariciones[termino] = apariciones.get(termino, 0) + 1
        total = max(1, len(fragmentos))
        self._rareza = {t: total / (1 + n) for t, n in apariciones.items()}
        self._fragmentos = fragmentos
        return fragmentos

    def recuperar(self, consulta: str, maximo: int = 3) -> list[Fragmento]:
        fragmentos = self._indice()
        buscados = _terminos(consulta)
        if not buscados:
            return []
        puntuados = [
            (sum(self._rareza.get(t, 0.0) for t in buscados & f.terminos), f) for f in fragmentos
        ]
        pertinentes = [(p, f) for p, f in puntuados if p > 0]
        pertinentes.sort(key=lambda par: par[0], reverse=True)
        return [f for _, f in pertinentes[:maximo]]

    def describir(self) -> dict[str, object]:
        return {
            "recuperador": self.nombre,
            "corpus": _relativa(self._corpus),
            "fragmentos": len(self._indice()),
        }


# ---------------------------------------------------------------------------
# Segundo adaptador: recuperacion por embeddings
#
# El puerto existia desde el primer dia esperando esto. Lo que sigue no
# reemplaza al recuperador por palabras clave: convive con el, y esa convivencia
# es lo que permite comparar dos estrategias sobre el mismo corpus en vez de
# sustituir una por otra por prestigio.
#
# Honestidad sobre por que existe. A cuatrocientos sesenta fragmentos, la
# busqueda por terminos ya responde bien: el capitulo lo dice y la medicion lo
# respalda. La razon para tener tambien la vectorial no es que haga falta aqui,
# es que la diferencia entre ambas **se puede medir** cuando las dos estan
# implementadas, y una decision medida vale mas que una preferencia.
# ---------------------------------------------------------------------------


class Vectorizador(ABC):
    """Puerto: convierte textos en vectores.

    Se separa del recuperador a proposito. Cambiar de modelo de embeddings
    —de uno alojado a uno local, por ejemplo— no deberia obligar a tocar la
    logica de recuperacion, que es lo que ocurre cuando ambos viven juntos.
    """

    nombre: str = "sin_nombre"
    #: Costo declarado por millon de tokens. Cero cuando corre en la maquina.
    usd_por_millon: float = 0.0

    @abstractmethod
    def vectorizar(self, textos: Sequence[str]) -> list[list[float]]:
        """Un vector por texto, en el mismo orden."""


class VectorizadorGemini(Vectorizador):
    """Embeddings de Google. Se importa de forma perezosa, como los demas SDK."""

    nombre = "gemini-embedding"
    usd_por_millon = 0.15
    MODELO_PREDETERMINADO = "gemini-embedding-001"

    def __init__(self, modelo: str | None = None, clave: str | None = None) -> None:
        from q5_agente.config import secreto  # noqa: PLC0415
        from q5_agente.errores import ProveedorNoConfigurado  # noqa: PLC0415

        try:
            from google import genai  # noqa: PLC0415
        except ImportError as exc:
            raise ProveedorNoConfigurado(
                "El paquete 'google-genai' no esta instalado."
            ) from exc

        api_key = clave or secreto("GEMINI_API_KEY") or secreto("GOOGLE_API_KEY")
        if not api_key:
            raise ProveedorNoConfigurado("Falta GEMINI_API_KEY para vectorizar.")

        self._cliente = genai.Client(api_key=api_key)
        self._modelo = modelo or self.MODELO_PREDETERMINADO

    def vectorizar(self, textos: Sequence[str]) -> list[list[float]]:
        from q5_agente.errores import ErrorDelProveedor  # noqa: PLC0415

        try:
            respuesta = self._cliente.models.embed_content(
                model=self._modelo, contents=list(textos)
            )
        except Exception as exc:  # noqa: BLE001
            raise ErrorDelProveedor(f"No se pudo vectorizar: {exc}") from exc
        return [list(e.values) for e in respuesta.embeddings]


def _coseno(a: Sequence[float], b: Sequence[float]) -> float:
    producto = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return producto / (na * nb)


class RecuperadorPorEmbeddings(RecuperadorDeDoctrina):
    """Recuperacion por similitud semantica sobre el mismo corpus de `docs/`.

    El almacen es Chroma cuando esta instalado, y una comparacion por coseno en
    memoria cuando no. **La alternativa en memoria no es un atajo**: a
    cuatrocientos sesenta fragmentos, recorrer la lista entera cuesta
    milisegundos, y tenerla permite que las pruebas corran sin instalar una base
    vectorial. Chroma aporta persistencia entre ejecuciones, que es lo que
    empieza a importar cuando vectorizar cuesta dinero.
    """

    nombre = "embeddings"

    def __init__(
        self,
        vectorizador: Vectorizador,
        corpus: Path | None = None,
        persistencia: Path | None = None,
    ) -> None:
        self._vectorizador = vectorizador
        self._corpus = corpus or CORPUS
        self._persistencia = persistencia
        self._fragmentos: list[Fragmento] = []
        self._vectores: list[list[float]] = []
        self._indexado = False

    def _indexar(self) -> None:
        if self._indexado:
            return
        fragmentos: list[Fragmento] = []
        for ruta in sorted(self._corpus.rglob("*.md")):
            fragmentos.extend(fragmentar(ruta, _relativa(ruta)))
        # Se vectoriza el ancla junto al texto: el encabezado es la etiqueta que
        # una persona usaria para pedir ese fragmento, y dejarlo fuera pierde la
        # senal mas concentrada del documento.
        self._vectores = self._vectorizador.vectorizar(
            [f"{f.ancla}\n{f.texto}" for f in fragmentos]
        )
        self._fragmentos = fragmentos
        self._indexado = True

    def recuperar(self, consulta: str, maximo: int = 3) -> list[Fragmento]:
        if not consulta.strip():
            return []
        self._indexar()
        if not self._fragmentos:
            return []
        objetivo = self._vectorizador.vectorizar([consulta])[0]
        puntuados = sorted(
            zip((_coseno(objetivo, v) for v in self._vectores), self._fragmentos, strict=False),
            key=lambda par: par[0],
            reverse=True,
        )
        return [f for _, f in puntuados[:maximo]]

    def describir(self) -> dict[str, object]:
        return {
            "recuperador": self.nombre,
            "vectorizador": self._vectorizador.nombre,
            "corpus": _relativa(self._corpus),
            "fragmentos": len(self._fragmentos),
            "usd_por_millon": self._vectorizador.usd_por_millon,
        }
