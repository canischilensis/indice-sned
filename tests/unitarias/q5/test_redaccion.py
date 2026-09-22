"""El texto que entrega el agente es prosa plana, venga del proveedor que venga.

Nace de un defecto observado el 2026-08-10 en la primera consulta real contra
Gemini: la respuesta llego en Markdown completo —negritas, encabezados, reglas
horizontales, listas anidadas— y la ventana la pinta sin interpretar marcado, de
modo que el directivo habria leido los asteriscos.

El mensaje de sistema le pide al modelo que no lo haga. Estas pruebas existen
porque esa peticion no es una garantia: verifican el unico punto donde el
contrato se puede cumplir con independencia del proveedor.
"""

# ruff: noqa: E501
# La muestra de mas abajo es una captura literal de lo que respondio el modelo.
# Reformatearla para caber en cien columnas la convertiria en otra cosa, y lo
# que se esta probando es precisamente su forma.

from __future__ import annotations

import pytest

from q5_agente.redaccion import a_prosa_plana, con_coma_decimal, sin_markdown

#: Fragmento textual de la respuesta de Gemini del 2026-08-10. Se conserva tal
#: cual porque un caso de prueba inventado no habria incluido la regla
#: horizontal ni la vineta anidada, que fueron las dos sorpresas.
RESPUESTA_REAL = """El factor **Superación** alcanza un valor estimado de **59.2** (con una ponderación del **28%**, aportando **16.58** puntos al Índice SNED).
*(Nota: Superación es un **factor acotado**, debido a que la corrección por significancia estadística no es publicada por el organismo emisor).*
---
### ¿Por qué se contrae este factor?
1. **Estancamiento y variaciones negativas en SIMCE:**
   * **Variación SIMCE Lectura 4° básico** (3.5 puntos de avance): contribuye con **-0.22** al factor.
"""


class TestMarcado:
    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("El factor **Superacion** cae", "El factor Superacion cae"),
            ("Es un __factor acotado__", "Es un factor acotado"),
            ("Una *nota* al margen", "Una nota al margen"),
            ("### Por que se contrae", "Por que se contrae"),
            ("## Sintesis", "Sintesis"),
            ("- Primer punto", "· Primer punto"),
            ("* Primer punto", "· Primer punto"),
            ("+ Primer punto", "· Primer punto"),
            ("El valor de `rbd` es ese", "El valor de rbd es ese"),
            ("Vea el [tablero](http://x/y) ahora", "Vea el tablero ahora"),
        ],
    )
    def test_se_retira_la_marca_y_se_conserva_el_contenido(self, entrada, esperado):
        assert sin_markdown(entrada) == esperado

    def test_la_regla_horizontal_desaparece(self):
        assert a_prosa_plana("Uno\n---\nDos") == "Uno\n\nDos"

    def test_la_sangria_de_una_vineta_anidada_se_conserva(self):
        """La sangria transmite jerarquia y el CSS respeta los espacios."""
        assert sin_markdown("   * Anidada") == "   · Anidada"

    def test_el_guion_bajo_suelto_no_se_toca(self):
        """Los nombres de variable del dominio lo llevan.

        Tratar `_` como marcado destruiria `tasa_aprobacion` y `falta_simce_2m`,
        que son identificadores reales que el agente cita al explicar un factor.
        """
        texto = "La variable falta_simce_2m resta, y tasa_aprobacion suma"
        assert sin_markdown(texto) == texto

    def test_la_respuesta_real_no_conserva_ninguna_marca(self):
        salida = a_prosa_plana(RESPUESTA_REAL)
        assert "**" not in salida
        assert "#" not in salida
        assert "---" not in salida
        assert "Superación" in salida
        assert "59,2" in salida


class TestSeparadorDecimal:
    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("59.2 puntos", "59,2 puntos"),
            ("aporta 16.58 al indice", "aporta 16,58 al indice"),
            ("contribuye con -0.22", "contribuye con -0,22"),
            ("puntaje 301.0 observado", "puntaje 301,0 observado"),
        ],
    )
    def test_el_decimal_pasa_a_coma(self, entrada, esperado):
        assert con_coma_decimal(entrada) == esperado

    def test_el_punto_final_de_la_frase_sobrevive(self):
        assert con_coma_decimal("El aporte es 16.58.") == "El aporte es 16,58."

    def test_un_grupo_de_millar_no_se_toca(self):
        """En castellano `4.435` son cuatro mil: convertirlo corromperia la cifra."""
        assert con_coma_decimal("4.435 tokens de entrada") == "4.435 tokens de entrada"

    def test_una_version_no_se_toca(self):
        assert con_coma_decimal("modelo 1.0.0 vigente") == "modelo 1.0.0 vigente"

    def test_tres_decimales_conservan_el_punto(self):
        """Limitacion declarada, no descuido.

        Tres digitos tras un punto son indistinguibles de un grupo de millar. Se
        prefiere no convertir antes que arriesgar corromper una cantidad, y
        queda escrito en el modulo.
        """
        assert con_coma_decimal("discrepancia de 0.0006") == "discrepancia de 0.0006"

    def test_una_fecha_no_se_toca(self):
        assert con_coma_decimal("del ciclo 2024. El siguiente") == "del ciclo 2024. El siguiente"


class TestProsaPlana:
    def test_el_texto_del_determinista_no_cambia(self):
        """El adaptador determinista ya cumple el contrato: aplicarlo no debe alterarlo."""
        texto = (
            "En el factor Superacion la estimacion es 59,20 sobre un valor base de 59,59. "
            "La aditividad quedo verificada."
        )
        assert a_prosa_plana(texto) == texto

    def test_es_idempotente(self):
        una = a_prosa_plana(RESPUESTA_REAL)
        assert a_prosa_plana(una) == una

    def test_no_produce_marcado_ejecutable(self):
        """Nunca se convierte a HTML: la salida de un modelo no se vuelve marcado."""
        salida = a_prosa_plana("Un **titulo** y un [enlace](http://x)")
        assert "<" not in salida and ">" not in salida
