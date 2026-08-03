"""Cuanto 1: reglas de cuarentena (Specification) y esqueleto de ingesta (Template Method).

Cada prueba verifica la PROPIEDAD que justifica el patron, no su forma.
Extraido de tests/test_patrones.py al reestructurar por tipo y por cuanto.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest



# ---------------------------------------------------------------------------
# P4 aplicado · reglas de cuarentena (CTRL-01)
# ---------------------------------------------------------------------------


def test_reglas_de_cuarentena_son_objetos_con_codigo():
    from q1_ingesta.reglas import REGLAS_BASE

    codigos = {r.codigo for r in REGLAS_BASE}
    assert codigos == {"rbd_ausente", "anio_ausente", "llave_duplicada"}
    assert all(r.descripcion for r in REGLAS_BASE)


def test_regla_de_ventana_temporal_es_componible():
    from q1_ingesta.calidad import aplicar_cuarentena
    from q1_ingesta.reglas import REGLAS_BASE, DentroDeVentanaTemporal

    df = pd.DataFrame(
        {
            "rbd": pd.array(["1", "2"], dtype="string"),
            "anio": [2024, 2024],
            "fecha": ["2024-03-01", "2025-12-31"],
        }
    )
    reglas = (*REGLAS_BASE, DentroDeVentanaTemporal("fecha", "2024-12-31"))
    validas, reporte = aplicar_cuarentena(df, "prueba", reglas=reglas, persistir=False)

    assert len(validas) == 1
    assert reporte.motivos == {"fuera_de_ventana": 1}
    assert "fuera_de_ventana" in reporte.reglas_aplicadas


def test_el_motivo_registrado_es_el_codigo_de_la_regla():
    from q1_ingesta.calidad import aplicar_cuarentena

    df = pd.DataFrame({"rbd": pd.array(["1", None, "1"], dtype="string"), "anio": [2024, 2024, 2024]})
    _, reporte = aplicar_cuarentena(df, "prueba", persistir=False)
    assert reporte.motivos == {"rbd_ausente": 1, "llave_duplicada": 1}


# ---------------------------------------------------------------------------
# P3 · Template Method
# ---------------------------------------------------------------------------


def test_template_method_aplica_los_controles_aunque_la_subclase_no_los_invoque(tmp_path):
    """La garantia del patron: una subclase no puede saltarse CTRL-01."""
    from q1_ingesta.fuentes import Fuente
    from q1_ingesta.ingestor import IngestorDeFuente

    fuente = Fuente("demo", "Demo", "org", "demo", "*.csv", ("rbd", "anio"), "anual")

    class IngestorDescuidado(IngestorDeFuente):
        """Solo implementa la lectura. No valida nada."""

        def _leer_archivo(self, ruta: Path) -> pd.DataFrame:
            return pd.DataFrame(
                {"RBD": pd.array(["0845", None, "0845"], dtype="string"), "anio": [2024, 2024, 2024]}
            )

        def _localizar(self):
            return [tmp_path / "falso.csv"]

    validas, reporte = IngestorDescuidado(fuente).ejecutar(persistir=False)

    assert reporte.filas_leidas == 3
    assert reporte.filas_cuarentena == 2          # nulo + duplicado, aislados sin pedirlo
    assert validas["rbd"].tolist() == ["845"]     # ceros a la izquierda normalizados


def test_template_method_falla_si_no_hay_archivos():
    from q1_ingesta.fuentes import Fuente
    from q1_ingesta.ingestor import IngestorCsv

    fuente = Fuente("inexistente", "X", "org", "no_existe", "*.csv", ("rbd",), "anual")
    with pytest.raises(FileNotFoundError):
        IngestorCsv(fuente).ejecutar(persistir=False)

