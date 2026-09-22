"""El agente actua en nombre del usuario, no como una cuenta de servicio.

Es la condicion que hace admisible exponer el agente a un navegador. Sin
delegacion, CTRL-04 protegeria a la cuenta con la que el agente se autentica, y
un directivo alcanzaria por el agente establecimientos que la interfaz le niega.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient
from q5_agente.app import app
from q5_agente.errores import SesionExpirada
from q5_agente.fabrica import crear_puerta
from q5_agente.gateway import ServicioSnedGateway

TOKEN = "token-de-la-directora"


@pytest.fixture
def cliente():
    return TestClient(app)


# --- el gateway ------------------------------------------------------------


def test_el_gateway_exige_una_identidad():
    with pytest.raises(ValueError, match="token delegado o un par usuario/clave"):
        ServicioSnedGateway("http://127.0.0.1:8000")


def test_con_token_delegado_no_se_pide_un_token_propio():
    """El agente no negocia credenciales: reenvia la del usuario."""
    vistas: list[httpx.Request] = []

    def registrar(peticion: httpx.Request) -> httpx.Response:
        vistas.append(peticion)
        return httpx.Response(200, json={"rbd": "25520", "indice": 67.6})

    puerta = ServicioSnedGateway(
        "http://127.0.0.1:8000",
        token=TOKEN,
        cliente=httpx.Client(transport=httpx.MockTransport(registrar)),
    )
    puerta.obtener("/prediccion/25520")

    assert len(vistas) == 1, "no debe haber una llamada previa a /auth/token"
    assert vistas[0].headers["Authorization"] == f"Bearer {TOKEN}"
    assert "/auth/token" not in str(vistas[0].url)


def test_un_token_delegado_vencido_no_se_renueva_solo():
    """Renovar por cuenta propia seria suplantar al usuario."""
    puerta = ServicioSnedGateway("http://127.0.0.1:8000", token=TOKEN)
    with pytest.raises(SesionExpirada, match="Vuelva a iniciar sesion"):
        puerta.autenticar()


def test_sin_token_la_fabrica_usa_la_cuenta_de_servicio():
    """La consola no tiene usuario detras: ahi la cuenta propia es lo correcto."""
    puerta = crear_puerta()
    assert isinstance(puerta, ServicioSnedGateway)
    assert puerta._delegado is False  # noqa: SLF001 - se verifica el modo elegido


def test_con_token_la_fabrica_delega():
    puerta = crear_puerta(token=TOKEN)
    assert puerta._delegado is True  # noqa: SLF001


# --- el servicio HTTP ------------------------------------------------------


def test_la_ruta_del_asesor_rechaza_una_consulta_sin_credencial(cliente):
    respuesta = cliente.post("/asesor/consulta", json={"rbd": "25520", "texto": "diagnostico"})
    assert respuesta.status_code == 401
    assert "Inicie sesion" in respuesta.json()["detail"]


def test_la_ruta_del_asesor_rechaza_un_esquema_de_autorizacion_ajeno(cliente):
    respuesta = cliente.post(
        "/asesor/consulta",
        json={"rbd": "25520", "texto": "diagnostico"},
        headers={"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="},
    )
    assert respuesta.status_code == 401


def test_la_ruta_de_salud_declara_que_la_identidad_es_delegada(cliente):
    assert "delegada" in cliente.get("/salud").json()["identidad"]


# --- ciclo de vida de la conexion ------------------------------------------


def test_la_puerta_se_cierra_al_terminar_la_peticion():
    """Un agente por peticion implica un cliente HTTP por peticion.

    Sin cierre, cada consulta dejaba conexiones vivas hasta que pasara el
    recolector. En Windows eso aparecia ademas como un "access violation" en un
    hilo secundario dentro de httpx durante el apagado del interprete.
    """
    from q5_agente.app import puerta_para

    with puerta_para(TOKEN) as puerta:
        assert puerta._cliente.is_closed is False  # noqa: SLF001
    assert puerta._cliente.is_closed is True  # noqa: SLF001


def test_la_puerta_se_cierra_aunque_la_consulta_falle():
    from q5_agente.app import puerta_para

    with pytest.raises(RuntimeError), puerta_para(TOKEN) as puerta:
        guardada = puerta
        raise RuntimeError("fallo a mitad de camino")
    assert guardada._cliente.is_closed is True  # noqa: SLF001


def test_cerrar_puerta_tolera_un_doble_sin_metodo_cerrar():
    """Los dobles de prueba no sostienen conexiones y no deben declarar el metodo."""
    from q5_agente.gateway import cerrar_puerta

    class DobleSinCerrar:
        def obtener(self, ruta, parametros=None):
            return {}

        def enviar(self, ruta, cuerpo):
            return {}

    cerrar_puerta(DobleSinCerrar())  # no debe lanzar


def test_el_gateway_sirve_como_gestor_de_contexto():
    puerta = ServicioSnedGateway("http://127.0.0.1:8000", token=TOKEN)
    with puerta as abierta:
        assert abierta is puerta
    assert puerta._cliente.is_closed is True  # noqa: SLF001
