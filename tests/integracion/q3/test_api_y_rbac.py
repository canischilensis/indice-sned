"""QA-C: pruebas sobre el servicio y el RBAC (CTRL-04)."""

import pytest
from fastapi.testclient import TestClient

from q3_servicio.main import app

pytestmark = pytest.mark.api
cliente = TestClient(app)


def _token(usuario: str) -> str:
    r = cliente.post("/api/v1/auth/token", data={"username": usuario, "password": "demo"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_salud_responde():
    r = cliente.get("/api/v1/salud")
    assert r.status_code == 200 and r.json()["estado"] == "operativo"


def test_catalogo_expone_las_ponderaciones_como_dato():
    r = cliente.get("/api/v1/catalogo/factores")
    assert r.status_code == 200
    assert len(r.json()["factores"]) == 6


def test_sin_token_no_hay_acceso():
    assert cliente.get("/api/v1/prediccion/8451").status_code == 401


def test_credenciales_invalidas_rechazadas():
    r = cliente.post("/api/v1/auth/token", data={"username": "directora.demo", "password": "mala"})
    assert r.status_code == 401


def test_rbac_bloquea_rbd_fuera_de_jurisdiccion():
    """CTRL-04: un fallo aqui reprueba la compuerta 2 del incremento."""
    cabeceras = {"Authorization": f"Bearer {_token('directora.demo')}"}
    r = cliente.get("/api/v1/prediccion/99999", headers=cabeceras)
    assert r.status_code == 403


def test_auditor_ve_cualquier_rbd():
    cabeceras = {"Authorization": f"Bearer {_token('auditor.demo')}"}
    r = cliente.get("/api/v1/prediccion/99999", headers=cabeceras)
    assert r.status_code != 403
