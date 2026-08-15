"""El tercer conjunto de cifras: lo que dice un documento no es una medicion.

G-02 era binario: una cifra estaba respaldada por una herramienta o era una
invencion. Con una herramienta que lee la documentacion del proyecto ese binario
deja de alcanzar, porque los documentos **contienen cifras** —el R2 declarado,
las tablas del esquema, el porcentaje de ponderacion acotada— y son verdaderas
cuando se escribieron, no necesariamente hoy.

Sin distinguirlas, la auditoria diria «fundada» sobre un archivo de marzo con la
misma autoridad que sobre una consulta al motor hecha hace un segundo.

Estas pruebas fijan los tres veredictos y la frontera del corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from q5_agente.contrato import Consulta
from q5_agente.doctrina import (
    RecuperadorDeDoctrina,
    RecuperadorPorEmbeddings,
    RecuperadorPorPalabrasClave,
    Vectorizador,
    fragmentar,
)
from q5_agente.guardarrailes import (
    ATRIBUIDA,
    FUNDADA,
    INFUNDADA,
    CifrasFundadasEnHerramientas,
    Fundamentacion,
    PoliticaDeSalida,
    SanitizadorDeParametros,
)
from q5_agente.herramientas.catalogo import ConsultaDeDoctrina, construir_catalogo

pytestmark = pytest.mark.agente

DOCUMENTO = "docs/prueba/DOCTRINA_DE_PRUEBA.md"


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """Corpus minimo y propio: el real cambia y estas pruebas no deben depender de el."""
    carpeta = tmp_path / "docs"
    carpeta.mkdir()
    (carpeta / "ADR-PRUEBA.md").write_text(
        "# ADR-PRUEBA · Por que el factor esta acotado\n\n"
        "## Contexto\n\n"
        "La correccion por significancia no se publica. El coeficiente declarado es 0,583 "
        "y el 63 % de la ponderacion queda acotada.\n\n"
        "## Decision\n\n"
        "Se declara la limitacion en vez de estimarla.\n",
        encoding="utf-8",
    )
    return carpeta


class _RecuperadorFijo(RecuperadorDeDoctrina):
    """Doble del puerto de recuperacion. Devuelve siempre el mismo fragmento."""

    nombre = "fijo"

    def __init__(self, fragmentos):
        self._fragmentos = fragmentos

    def recuperar(self, consulta, maximo=3):
        return self._fragmentos[:maximo]


class TestFragmentacion:
    def test_el_encabezado_es_el_ancla(self, corpus: Path):
        fragmentos = fragmentar(corpus / "ADR-PRUEBA.md", DOCUMENTO)
        anclas = [f.ancla for f in fragmentos]

        assert "Contexto" in anclas
        assert "Decision" in anclas

    def test_cada_cifra_viaja_con_su_procedencia(self, corpus: Path):
        contexto = next(
            f for f in fragmentar(corpus / "ADR-PRUEBA.md", DOCUMENTO) if f.ancla == "Contexto"
        )
        procedencias = {p.valor: p for p in contexto.procedencias()}

        assert 0.583 in procedencias
        assert 63.0 in procedencias
        assert procedencias[0.583].documento == DOCUMENTO
        assert procedencias[0.583].ancla == "Contexto"
        assert procedencias[0.583].huella, "sin huella no se detecta que el texto cambio"

    def test_un_entero_de_un_digito_no_es_magnitud(self, corpus: Path):
        """Mismo criterio que G-02: no se registra el 'seis' de 'los seis factores'."""
        fragmentos = fragmentar(corpus / "ADR-PRUEBA.md", DOCUMENTO)
        valores = [p.valor for f in fragmentos for p in f.procedencias()]

        assert all(abs(v) >= 10 or not float(v).is_integer() for v in valores)


class TestRecuperacion:
    def test_encuentra_el_fragmento_pertinente(self, corpus: Path):
        recuperador = RecuperadorPorPalabrasClave(corpus)
        fragmentos = recuperador.recuperar("por que el factor esta acotado", 2)

        assert fragmentos
        assert any("acotada" in f.texto or "acotado" in f.ancla for f in fragmentos)

    def test_una_consulta_sin_terminos_utiles_no_devuelve_nada(self, corpus: Path):
        assert RecuperadorPorPalabrasClave(corpus).recuperar("de la y el", 3) == []


class TestHerramientaDeDoctrina:
    def _herramienta(self, corpus: Path) -> ConsultaDeDoctrina:
        return ConsultaDeDoctrina(RecuperadorPorPalabrasClave(corpus))

    def test_las_cifras_salen_por_el_tercer_conjunto(self, corpus: Path):
        """La frontera entera del diseno esta en esta asercion.

        Si estas cifras entraran por `cifras`, G-02 las trataria como respaldadas
        por el motor y un archivo se convertiria en una medicion.
        """
        resultado = self._herramienta(corpus).ejecutar(consulta="por que el factor esta acotado")

        assert resultado.exito
        assert resultado.cifras == set(), "una cifra de documento no es dato del motor"
        assert 0.583 in resultado.cifras_documentales
        assert resultado.procedencias

    def test_declara_cuando_no_cubre_la_consulta(self, corpus: Path):
        resultado = self._herramienta(corpus).ejecutar(consulta="cuantos estudiantes hay")

        assert not resultado.exito
        assert "no cubre" in (resultado.error or "")

    def test_no_entra_al_catalogo_si_no_se_le_entrega_recuperador(self):
        """Agregar una herramienta cambia el ruteo: no debe ocurrir por accidente."""
        catalogo = construir_catalogo(object(), SanitizadorDeParametros())

        assert "consulta_de_doctrina" not in catalogo

    def test_entra_cuando_se_le_entrega(self, corpus: Path):
        catalogo = construir_catalogo(
            object(), SanitizadorDeParametros(), RecuperadorPorPalabrasClave(corpus)
        )

        assert "consulta_de_doctrina" in catalogo


class TestTresVeredictos:
    _g = CifrasFundadasEnHerramientas()

    def _veredicto(self, texto: str, datos=frozenset(), docs=frozenset(), nombres=()) -> str:
        candidato = Fundamentacion(texto, set(datos), set(docs), nombres)
        return self._g.veredictos(candidato)[0][1]

    def test_una_cifra_del_motor_es_fundada(self):
        assert self._veredicto("El indice es 69,36 puntos.", datos={69.36}) == FUNDADA

    def test_una_cifra_de_documento_sin_atribuir_es_infundada(self):
        veredicto = self._veredicto(
            "El coeficiente es 0,583.", docs={0.583}, nombres=(DOCUMENTO,)
        )
        assert veredicto == INFUNDADA

    def test_una_cifra_de_documento_atribuida_se_acepta(self):
        veredicto = self._veredicto(
            "Segun DOCTRINA_DE_PRUEBA, el coeficiente es 0,583.",
            docs={0.583},
            nombres=(DOCUMENTO,),
        )
        assert veredicto == ATRIBUIDA

    def test_la_atribucion_se_exige_en_la_misma_oracion(self):
        """Si el documento se nombra tres frases antes, quien lee el numero no lo ve."""
        veredicto = self._veredicto(
            "Consulte DOCTRINA_DE_PRUEBA. El coeficiente es 0,583.",
            docs={0.583},
            nombres=(DOCUMENTO,),
        )
        assert veredicto == INFUNDADA

    def test_una_cifra_que_no_esta_en_ninguna_parte_sigue_siendo_infundada(self):
        assert self._veredicto("El indice es 88,88.") == INFUNDADA

    def test_el_motivo_del_rechazo_distingue_los_dos_casos(self):
        """Inventar una cifra y no atribuirla se corrigen distinto."""
        politica = PoliticaDeSalida()
        _, _, motivo = politica.evaluar(
            "El coeficiente es 0,583.", set(), {0.583}, (DOCUMENTO,)
        )

        assert "no nombra el documento" in (motivo or "")

    def test_sin_documentacion_el_comportamiento_historico_no_cambia(self):
        """Quien no consulte doctrina no debe notar que el tercer conjunto existe."""
        politica = PoliticaDeSalida()

        assert politica.evaluar("El indice es 69,36.", {69.36})[0]
        assert not politica.evaluar("El indice es 88,88.", {69.36})[0]


def test_la_respuesta_transporta_el_tercer_conjunto(corpus: Path):
    """La traza llega hasta la pantalla: si no viaja aqui, no se puede marcar alla."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluacion"))
    from dobles import ServicioFalso  # noqa: PLC0415
    from q5_agente.bucle import AgenteDeBucleSimple  # noqa: PLC0415
    from q5_agente.proveedores.determinista import AdaptadorDeterminista  # noqa: PLC0415

    herramientas = construir_catalogo(
        ServicioFalso(), SanitizadorDeParametros(), RecuperadorPorPalabrasClave(corpus)
    )
    proveedor = AdaptadorDeterminista({h.nombre: h.disparadores for h in herramientas.values()})
    agente = AgenteDeBucleSimple(proveedor, herramientas, PoliticaDeSalida(), max_pasos=3)

    respuesta = agente.asesorar(
        Consulta(texto="Que dice la documentacion y que decision quedo registrada", rbd="9")
    )

    assert hasattr(respuesta, "cifras_documentales")
    assert hasattr(respuesta, "documentos_consultados")


class _VectorizadorFalso(Vectorizador):
    """Vectoriza contando terminos compartidos con un vocabulario fijo.

    No imita a un modelo real y no pretende hacerlo: existe para que las pruebas
    del recuperador vectorial corran sin red, sin clave y sin costo. Lo que
    verifican es el contrato del puerto y la mecanica del indice, no la calidad
    semantica, que solo se puede medir con un modelo de verdad.
    """

    nombre = "falso"
    VOCABULARIO = ("acotad", "factor", "signif", "decisi", "limita", "conte")

    def vectorizar(self, textos):
        plano = [t.lower() for t in textos]
        return [[float(t.count(p)) for p in self.VOCABULARIO] for t in plano]


class TestSegundoAdaptadorDeRecuperacion:
    """El puerto de recuperacion tiene dos implementaciones, como el de datos."""

    def test_ambos_implementan_el_mismo_puerto(self, corpus: Path):
        porPalabras = RecuperadorPorPalabrasClave(corpus)
        porVectores = RecuperadorPorEmbeddings(_VectorizadorFalso(), corpus)

        assert isinstance(porPalabras, RecuperadorDeDoctrina)
        assert isinstance(porVectores, RecuperadorDeDoctrina)

    def test_el_vectorial_recupera_del_mismo_corpus(self, corpus: Path):
        fragmentos = RecuperadorPorEmbeddings(_VectorizadorFalso(), corpus).recuperar(
            "por que el factor esta acotado", 2
        )

        assert fragmentos
        assert all(f.documento.endswith("ADR-PRUEBA.md") for f in fragmentos)

    def test_los_fragmentos_conservan_su_procedencia(self, corpus: Path):
        """La procedencia es del fragmento, no de la estrategia que lo encontro.

        Si dependiera del recuperador, cambiar de estrategia cambiaria lo que la
        auditoria puede afirmar sobre una misma cifra.
        """
        fragmentos = RecuperadorPorEmbeddings(_VectorizadorFalso(), corpus).recuperar(
            "coeficiente declarado", 3
        )
        procedencias = [p for f in fragmentos for p in f.procedencias()]

        assert any(p.valor == 0.583 for p in procedencias)
        assert all(p.documento and p.ancla for p in procedencias)

    def test_una_consulta_vacia_no_vectoriza(self, corpus: Path):
        """Vectorizar cuesta dinero: una consulta vacia no debe gastarlo."""
        assert RecuperadorPorEmbeddings(_VectorizadorFalso(), corpus).recuperar("  ", 3) == []

    def test_declara_su_costo(self, corpus: Path):
        descripcion = RecuperadorPorEmbeddings(_VectorizadorFalso(), corpus).describir()

        assert descripcion["recuperador"] == "embeddings"
        assert "usd_por_millon" in descripcion, "el costo se declara, no se descubre en la factura"
