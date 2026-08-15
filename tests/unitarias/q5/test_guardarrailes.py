"""G-01, G-02 y G-03: una prueba por regla, y una por su composicion."""

import pytest
from q5_agente.errores import ParametroInvalido
from q5_agente.guardarrailes import (
    CifrasFundadasEnHerramientas,
    Fundamentacion,
    PoliticaDeSalida,
    SanitizadorDeParametros,
    SinPromesasDeRetorno,
    extraer_magnitudes,
)

# --- G-01 -------------------------------------------------------------------


def test_el_rbd_debe_ser_numerico_y_acotado():
    san = SanitizadorDeParametros()
    with pytest.raises(ParametroInvalido):
        san.limpiar("cualquiera", {"rbd": "25520; DROP TABLE core.establecimiento"})


def test_el_periodo_exige_forma_de_bienio():
    san = SanitizadorDeParametros()
    with pytest.raises(ParametroInvalido):
        san.limpiar("cualquiera", {"rbd": "25520", "periodo": "2024"})


def test_el_objetivo_del_modelo_no_puede_entrar_como_parametro():
    """CTRL-02 tambien rige para el agente: el indice no es una palanca."""
    san = SanitizadorDeParametros()
    with pytest.raises(ParametroInvalido, match="objetivo o agrupacion"):
        san.limpiar("simulacion", {"rbd": "25520", "variables": {"indicer": 100}})


def test_una_variable_fuera_del_catalogo_se_rechaza():
    san = SanitizadorDeParametros()
    with pytest.raises(ParametroInvalido, match="catalogo de variables"):
        san.limpiar("simulacion", {"rbd": "25520", "variables": {"presupuesto_sep": 1000}})


def test_un_valor_no_finito_se_rechaza():
    san = SanitizadorDeParametros()
    with pytest.raises(ParametroInvalido):
        san.limpiar("simulacion", {"rbd": "25520", "variables": {"tasa_aprobacion": float("inf")}})


def test_el_escenario_tiene_tope_de_variables():
    san = SanitizadorDeParametros(maximo_variables=2)
    with pytest.raises(ParametroInvalido, match="a lo mas 2"):
        san.limpiar(
            "simulacion",
            {
                "rbd": "25520",
                "variables": {"tasa_aprobacion": 90, "tasa_retiro": 2, "idps_clima": 70},
            },
        )


def test_los_parametros_validos_pasan_normalizados():
    san = SanitizadorDeParametros()
    limpio = san.limpiar(
        "simulacion",
        {"rbd": " 25520 ", "periodo": "2024-2025", "variables": {" Tasa_Aprobacion ": "96,4"}},
    )
    assert limpio["rbd"] == "25520"
    assert limpio["periodo"] == "2024-2025"
    assert limpio["variables"] == {"tasa_aprobacion": pytest.approx(96.4)}


# --- G-02 -------------------------------------------------------------------


def test_los_enteros_de_un_digito_no_cuentan_como_magnitud():
    """Evita rechazar enumeraciones: 'los 6 factores' no es una cifra citada."""
    assert extraer_magnitudes("Los 6 factores y las 3 ventanas") == []


def test_reconoce_decimales_con_coma_y_con_punto():
    assert extraer_magnitudes("El indice es 67,60 y el error 2.31") == [67.60, 2.31]


def test_una_cifra_que_ninguna_herramienta_devolvio_se_detecta():
    regla = CifrasFundadasEnHerramientas()
    candidato = Fundamentacion("El indice estimado es 71,40 puntos.", {67.60, 2.31})
    assert not regla.es_satisfecha_por(candidato)
    assert regla.cifras_sin_respaldo(candidato) == [71.40]


def test_una_proporcion_respalda_su_porcentaje():
    regla = CifrasFundadasEnHerramientas()
    candidato = Fundamentacion("Efectividad pesa 37 por ciento.", {0.37})
    assert regla.es_satisfecha_por(candidato)


def test_el_signo_viaja_en_la_prosa_no_en_la_magnitud():
    regla = CifrasFundadasEnHerramientas()
    candidato = Fundamentacion("Los procesos con sancion restan 1,20 puntos.", {-1.20})
    assert regla.es_satisfecha_por(candidato)


# --- G-03 -------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "Le garantizo que obtendra el beneficio.",
        "Con esto aseguramos la excelencia el proximo ciclo.",
        "Si sube ese puntaje, ganara el SNED.",
    ],
)
def test_las_promesas_de_retorno_se_detectan(texto):
    regla = SinPromesasDeRetorno()
    assert not regla.es_satisfecha_por(Fundamentacion(texto))


def test_una_lectura_prudente_no_es_una_promesa():
    regla = SinPromesasDeRetorno()
    texto = (
        "El beneficio se asigna por posicion relativa dentro del Grupo Homogeneo, de modo que "
        "ninguna mejora asegura el cambio de tramo."
    )
    assert regla.es_satisfecha_por(Fundamentacion(texto))


@pytest.mark.parametrize(
    "texto",
    [
        "Ninguna mejora garantiza la obtencion del beneficio.",
        "No puedo garantizarle el beneficio: depende de la posicion relativa.",
        "Nadie garantiza el cambio de tramo, porque el grupo tambien se mueve.",
        "Subir ese factor ayuda, pero sin garantizar el resultado.",
        "Nunca voy a garantizar que obtendra el beneficio.",
    ],
)
def test_advertir_que_nadie_promete_no_es_prometer(texto):
    """Defecto encontrado en produccion: G-03 retenia la frase correcta.

    La version anterior buscaba la raiz en el texto completo, sin mirar si venia
    negada. Como el propio mensaje de sistema le ensena al modelo que "ninguna
    mejora lo garantiza", el modelo parafraseaba la instruccion y la respuesta
    se bloqueaba. La prueba de la lectura prudente no lo detectaba porque estaba
    escrita con "asegura", esquivando justo la palabra que fallaba.
    """
    regla = SinPromesasDeRetorno()
    assert regla.es_satisfecha_por(Fundamentacion(texto))


@pytest.mark.parametrize(
    "texto",
    [
        "No hay duda: le garantizo el beneficio.",
        "No se preocupe. Le garantizo el beneficio.",
        "Ninguna otra medida hace falta, le garantizo el beneficio.",
    ],
)
def test_una_negacion_que_no_rige_sobre_la_promesa_no_la_salva(texto):
    """Aceptar la negacion no puede convertirse en una llave para desactivar G-03.

    La negacion debe regir sobre la promesa: misma oracion, sin puntuacion de
    por medio y a corta distancia. Anteponer un "no" cualquiera no basta.
    """
    regla = SinPromesasDeRetorno()
    assert not regla.es_satisfecha_por(Fundamentacion(texto))


def test_el_rechazo_cita_la_oracion_completa():
    """Sin la oracion, un rechazo de G-03 es inauditable."""
    politica = PoliticaDeSalida()
    _, _, motivo = politica.evaluar("Le garantizo el beneficio este ciclo.", set())
    assert "Le garantizo el beneficio este ciclo." in motivo


def test_el_mensaje_de_sistema_cumple_su_propia_politica():
    """Lo que se le prohibe al modelo no puede estar escrito en la instruccion.

    Esta es la prueba que habria evitado el defecto: el mensaje de sistema usaba
    la raiz que G-03 vigila, y el modelo la repetia por obediencia.
    """
    from q5_agente.prompts import SISTEMA

    regla = SinPromesasDeRetorno()
    assert regla.es_satisfecha_por(Fundamentacion(SISTEMA))


# --- composicion ------------------------------------------------------------


def test_la_politica_rechaza_primero_la_promesa_y_luego_la_cifra():
    politica = PoliticaDeSalida()
    aceptado, codigo, motivo = politica.evaluar("Le garantizo 99,90 puntos.", set())
    assert not aceptado
    assert codigo == "G-03"
    assert "promet" in motivo.lower()


def test_la_politica_acepta_un_texto_fundado_y_prudente():
    politica = PoliticaDeSalida()
    aceptado, codigo, motivo = politica.evaluar(
        "El indice estimado es 67,60 puntos, con un error medio de 2,31.", {67.60, 2.31}
    )
    assert aceptado and codigo is None and motivo is None


def test_las_reglas_se_componen_con_el_puerto_especificacion():
    """Las tres barreras son Especificacion, igual que la cuarentena y las alertas."""
    politica = PoliticaDeSalida()
    combinada = politica.especificacion
    assert combinada.es_satisfecha_por(Fundamentacion("Sin cifras y sin promesas.", set()))
    assert not combinada.es_satisfecha_por(Fundamentacion("Garantizado: 88,80.", set()))
