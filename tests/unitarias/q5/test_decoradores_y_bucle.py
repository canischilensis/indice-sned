"""Decoradores del proveedor y comportamiento del bucle."""

import pytest
from q5_agente.bucle import AgenteDeBucleSimple
from q5_agente.contrato import Consulta
from q5_agente.decoradores import ProveedorConCortacircuitos, ProveedorInstrumentado
from q5_agente.errores import CircuitoAbierto, ErrorDelProveedor, ParametroInvalido
from q5_agente.guardarrailes import SanitizadorDeParametros
from q5_agente.herramientas.contrato import Herramienta, ResultadoHerramienta
from q5_agente.proveedores.contrato import (
    PeticionDeHerramienta,
    ProveedorDeModelo,
    RespuestaDelModelo,
)


class ProveedorDoble(ProveedorDeModelo):
    """Devuelve una secuencia fijada de pasos, o falla siempre."""

    nombre = "doble"
    usd_por_millon_entrada = 3.0
    usd_por_millon_salida = 15.0

    def __init__(self, pasos=None, falla=False):
        self.pasos = list(pasos or [])
        self.falla = falla
        self.invocaciones = 0

    def completar(self, mensajes, herramientas):
        self.invocaciones += 1
        if self.falla:
            raise ErrorDelProveedor("el proveedor no responde")
        if self.pasos:
            return self.pasos.pop(0)
        return RespuestaDelModelo(texto="sin novedad", tokens_entrada=100, tokens_salida=50)


class HerramientaDoble(Herramienta):
    nombre = "diagnostico_de_establecimiento"
    descripcion = "doble"
    disparadores = ("diagnostico",)

    def __init__(self):
        self.recibido = None

    def esquema(self):
        return {"type": "object", "properties": {"rbd": {"type": "string"}}}

    def ejecutar(self, **parametros):
        self.recibido = parametros
        return ResultadoHerramienta.desde(self.nombre, {"indice": 67.60}, "doble")


class RelojFalso:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def avanzar(self, segundos):
        self.t += segundos


# --- instrumentacion --------------------------------------------------------


def test_la_instrumentacion_acumula_tokens_costo_y_latencia():
    reloj = RelojFalso()
    base = ProveedorDoble()
    medido = ProveedorInstrumentado(base, reloj=reloj)

    medido.completar([], [])
    medido.completar([], [])

    assert medido.consumo.llamadas == 2
    assert medido.consumo.tokens_entrada == 200
    assert medido.consumo.tokens_salida == 100
    assert medido.consumo.costo_usd == pytest.approx(200 / 1e6 * 3.0 + 100 / 1e6 * 15.0)
    assert len(medido.consumo.por_llamada) == 2


def test_la_instrumentacion_se_puede_reiniciar_por_consulta():
    medido = ProveedorInstrumentado(ProveedorDoble())
    medido.completar([], [])
    medido.reiniciar()
    assert medido.consumo.llamadas == 0


# --- cortacircuitos ---------------------------------------------------------


def test_el_circuito_abre_tras_el_umbral_de_fallos():
    reloj = RelojFalso()
    protegido = ProveedorConCortacircuitos(
        ProveedorDoble(falla=True), umbral_fallos=2, segundos_reposo=30, reloj=reloj
    )
    for _ in range(2):
        with pytest.raises(ErrorDelProveedor):
            protegido.completar([], [])
    assert protegido.estado == protegido.ABIERTO
    with pytest.raises(CircuitoAbierto):
        protegido.completar([], [])


def test_el_circuito_pasa_a_semiabierto_tras_el_reposo_y_cierra_con_exito():
    reloj = RelojFalso()
    base = ProveedorDoble(falla=True)
    protegido = ProveedorConCortacircuitos(base, umbral_fallos=1, segundos_reposo=30, reloj=reloj)

    with pytest.raises(ErrorDelProveedor):
        protegido.completar([], [])
    assert protegido.estado == protegido.ABIERTO

    reloj.avanzar(31)
    assert protegido.estado == protegido.SEMIABIERTO

    base.falla = False
    protegido.completar([], [])
    assert protegido.estado == protegido.CERRADO


def test_el_circuito_abierto_no_llama_al_proveedor():
    reloj = RelojFalso()
    base = ProveedorDoble(falla=True)
    protegido = ProveedorConCortacircuitos(base, umbral_fallos=1, segundos_reposo=30, reloj=reloj)
    with pytest.raises(ErrorDelProveedor):
        protegido.completar([], [])
    invocaciones = base.invocaciones
    with pytest.raises(CircuitoAbierto):
        protegido.completar([], [])
    assert base.invocaciones == invocaciones, "el circuito abierto debe cortar sin intentar"


# --- bucle ------------------------------------------------------------------


def _agente(proveedor, herramienta=None, max_pasos=3):
    herr = herramienta or HerramientaDoble()
    return AgenteDeBucleSimple(proveedor, {herr.nombre: herr}, max_pasos=max_pasos), herr


def test_el_rbd_de_la_sesion_manda_sobre_el_que_infiera_el_modelo():
    """Defensa contra la inyeccion por parametro: la sesion no es negociable."""
    pasos = [
        RespuestaDelModelo(
            peticion=PeticionDeHerramienta("diagnostico_de_establecimiento", {"rbd": "99999"})
        ),
        RespuestaDelModelo(texto="El indice estimado es 67,60 puntos."),
    ]
    agente, herramienta = _agente(ProveedorDoble(pasos))
    agente.asesorar(Consulta(texto="diagnostico", rbd="25520"))
    assert herramienta.recibido["rbd"] == "25520"


def test_una_herramienta_inexistente_no_rompe_el_bucle():
    pasos = [
        RespuestaDelModelo(peticion=PeticionDeHerramienta("herramienta_fantasma", {})),
        RespuestaDelModelo(texto="No dispongo de esa capacidad."),
    ]
    agente, _ = _agente(ProveedorDoble(pasos))
    respuesta = agente.asesorar(Consulta(texto="algo", rbd="25520"))
    assert respuesta.llamadas[0].exito is False
    assert not respuesta.rechazada


def test_el_bucle_respeta_el_maximo_de_pasos():
    pasos = [
        RespuestaDelModelo(peticion=PeticionDeHerramienta("diagnostico_de_establecimiento", {}))
        for _ in range(10)
    ]
    agente, _ = _agente(ProveedorDoble(pasos), max_pasos=2)
    respuesta = agente.asesorar(Consulta(texto="diagnostico", rbd="25520"))
    assert len(respuesta.llamadas) == 2


def test_si_el_proveedor_cae_el_agente_lo_dice_y_no_inventa():
    agente, _ = _agente(ProveedorDoble(falla=True))
    respuesta = agente.asesorar(Consulta(texto="diagnostico", rbd="25520"))
    assert respuesta.rechazada
    assert "G-04" in respuesta.guardarrailes_aplicados
    assert not respuesta.fundada_en_herramientas


def test_el_uso_se_agrega_a_lo_largo_de_los_pasos():
    pasos = [
        RespuestaDelModelo(
            peticion=PeticionDeHerramienta("diagnostico_de_establecimiento", {}),
            tokens_entrada=100, tokens_salida=10,
        ),
        RespuestaDelModelo(
            texto="El indice estimado es 67,60.", tokens_entrada=400, tokens_salida=80
        ),
    ]
    agente, _ = _agente(ProveedorDoble(pasos))
    respuesta = agente.asesorar(Consulta(texto="diagnostico", rbd="25520"))
    assert respuesta.uso.llamadas_al_modelo == 2
    assert respuesta.uso.tokens_entrada == 500
    assert respuesta.uso.tokens_salida == 90


def test_la_sanitizacion_se_aplica_aunque_el_modelo_pida_algo_invalido():
    """G-01 vive en la herramienta, no en la confianza depositada en el modelo."""
    san = SanitizadorDeParametros()
    with pytest.raises(ParametroInvalido):
        san.limpiar("simulacion", {"rbd": "25520", "variables": {"cluster_codigo": 12}})
