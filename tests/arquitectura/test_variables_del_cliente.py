"""Ninguna variable expuesta al navegador puede llevar nombre de secreto.

`vite.config.ts` declara `envDir: '../..'`, de modo que el cliente lee el mismo
`.env` que el resto del sistema. Es lo que hace que su configuracion sea real y
no una constante escondida en `api.ts`, pero pone al empaquetador a leer un
archivo que contiene el secreto de firma, la clave del proveedor y la credencial
de la base.

Vite protege ese archivo con una regla simple: **solo las variables con prefijo
`VITE_` entran en el paquete que se descarga el navegador**. La regla funciona.
Lo que no funciona solo es la convencion humana de no ponerle ese prefijo a un
secreto, y por eso existe esta prueba: la garantia depende de un nombre, y los
nombres se eligen con prisa.

No verifica el `.env` real —no se versiona— sino la plantilla, que es lo que
alguien copia. Un secreto mal prefijado en la plantilla se propaga a cada
instalacion.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]

#: Fragmentos que delatan una credencial. No pretende ser exhaustivo: pretende
#: atrapar el descuido tipico, que es prefijar por costumbre.
_NOMBRES_DE_SECRETO = ("key", "secret", "password", "passwd", "token", "clave", "credencial")

#: Solo se aceptan direcciones. Si manana el cliente necesita otra cosa, que la
#: discusion ocurra al agregar la excepcion y no despues de publicarla.
_PERMITIDAS = {"VITE_API_URL", "VITE_AGENTE_URL"}

_ASIGNACION = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", re.MULTILINE)


def _variables_de(ruta: Path) -> list[str]:
    if not ruta.is_file():
        return []
    return _ASIGNACION.findall(ruta.read_text(encoding="utf-8", errors="ignore"))


@pytest.fixture(scope="module")
def variables_expuestas() -> list[str]:
    plantilla = RAIZ / ".env.example"
    assert plantilla.is_file(), "la plantilla de configuracion debe estar versionada"
    return [v for v in _variables_de(plantilla) if v.startswith("VITE_")]


def test_la_plantilla_declara_las_variables_del_cliente(variables_expuestas):
    """Si desaparecen, el cliente vuelve a depender de constantes en el codigo."""
    assert variables_expuestas, "la plantilla no declara ninguna variable VITE_"


def test_ninguna_variable_expuesta_lleva_nombre_de_secreto(variables_expuestas):
    sospechosas = [
        v for v in variables_expuestas
        if any(palabra in v.lower() for palabra in _NOMBRES_DE_SECRETO)
    ]
    assert not sospechosas, (
        f"estas variables se empaquetarian en el navegador: {sospechosas}. "
        "Una credencial no lleva prefijo VITE_."
    )


def test_las_variables_expuestas_estan_declaradas_una_a_una(variables_expuestas):
    """Ampliar lo que viaja al navegador es una decision, no un descuido."""
    nuevas = set(variables_expuestas) - _PERMITIDAS
    assert not nuevas, (
        f"variables VITE_ no declaradas en esta prueba: {sorted(nuevas)}. "
        "Agreguelas a _PERMITIDAS si su exposicion al navegador es deliberada."
    )


def test_el_cliente_no_tiene_un_env_propio_que_compita():
    """Dos archivos de configuracion para lo mismo divergen sin avisar.

    `envDir` apunta a la raiz. Un `.env` dentro de la carpeta del cliente no seria
    leido y quedaria como documentacion falsa de lo que el sistema usa.
    """
    propio = RAIZ / "quanta" / "q4_cliente" / ".env"
    assert not propio.is_file(), (
        "existe quanta/q4_cliente/.env y Vite no lo lee: envDir apunta a la raiz"
    )
