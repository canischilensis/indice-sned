"""Doble del servicio del indice para evaluar el agente sin red ni base de datos.

Devuelve cargas con la misma forma que los esquemas publicados del cuanto 3, y
reproduce sus condiciones de error: 403 fuera de jurisdiccion, 404 para un RBD
depurado, 422 para una variable no simulable y 503 cuando falta el artefacto.

Las cifras son de demostracion y estan declaradas como tales. Lo que la
evaluacion mide no es su exactitud, sino que el agente no cite ninguna cifra
que este doble no haya devuelto.
"""

from __future__ import annotations

from typing import Any

from q5_agente.errores import (
    EstablecimientoNoEncontrado,
    FueraDeJurisdiccion,
    ParametroInvalido,
    ServicioNoDisponible,
)

#: Muestra congelada del arnes de paridad (tests/paridad/muestra.json).
RBDS_MUESTRA = [
    "9", "10", "11", "31", "381", "1418", "2829", "2997", "3215", "3640",
    "4288", "4432", "4505", "7388", "8376", "9911", "16816", "16942", "20008", "26110",
]

#: Casos borde declarados en la propia muestra.
SIN_MEDICION_2M = "9"
CAMBIA_CLUSTER = "10"
TRAMO_100 = "11"
RURAL = "31"

#: RBD que existe pero esta fuera de la jurisdiccion del usuario de la sesion.
RBD_AJENO = "99999"
#: RBD dentro de la jurisdiccion que no sobrevivio a la depuracion.
RBD_DEPURADO = "8451"
#: RBD cuyo artefacto de modelo no esta disponible.
RBD_SIN_ARTEFACTO = "16942"

FACTORES = [
    {"codigo": "EFECTIVR", "nombre": "Efectividad", "peso": 0.37, "valor": 71.20,
     "aporte_al_indice": 26.34, "es_acotado": False, "restriccion": None},
    {"codigo": "SUPERACR", "nombre": "Superacion", "peso": 0.28, "valor": 58.40,
     "aporte_al_indice": 16.35, "es_acotado": True,
     "restriccion": "Correccion por significancia estadistica no publicada"},
    {"codigo": "IGUALDAR", "nombre": "Igualdad de oportunidades", "peso": 0.22, "valor": 64.10,
     "aporte_al_indice": 14.10, "es_acotado": True,
     "restriccion": "Subtipo de sancion por discriminacion no desagregado"},
    {"codigo": "INICIATR", "nombre": "Iniciativa", "peso": 0.06, "valor": 60.00,
     "aporte_al_indice": 3.60, "es_acotado": True,
     "restriccion": "Ficha de autorreporte no publica"},
    {"codigo": "INTEGRAR", "nombre": "Integracion y participacion", "peso": 0.05, "valor": 62.50,
     "aporte_al_indice": 3.13, "es_acotado": True,
     "restriccion": "Ficha de autorreporte no publica"},
    {"codigo": "MEJORAMR", "nombre": "Mejoramiento", "peso": 0.02, "valor": 55.00,
     "aporte_al_indice": 1.10, "es_acotado": True, "restriccion": "Varianza proxima a cero"},
]

VARIABLES_SIMULABLES = {
    "simce_mat_4b", "simce_leng_4b", "tasa_aprobacion", "tasa_retiro",
    "tasa_asistencia", "idps_clima", "dotacion_docente",
}


class ServicioFalso:
    """Implementa el protocolo PuertaDeServicio sin salir del proceso."""

    def __init__(self, jurisdiccion: list[str] | None = None) -> None:
        # El RBD depurado SI esta bajo jurisdiccion: por eso responde 404 y no
        # 403. Distinguir ambas condiciones es justamente lo que se evalua.
        self.jurisdiccion = set(jurisdiccion or [*RBDS_MUESTRA, RBD_DEPURADO])
        self.llamadas: list[tuple[str, dict[str, Any]]] = []

    # --- protocolo --------------------------------------------------------

    def obtener(self, ruta: str, parametros: dict[str, Any] | None = None) -> dict:
        self.llamadas.append((ruta, dict(parametros or {})))
        partes = [p for p in ruta.split("/") if p]
        rbd = partes[1] if len(partes) > 1 else ""
        self._exigir(rbd)

        if ruta.endswith("/alertas"):
            return {"rbd": rbd, "alertas": self._alertas(rbd)}
        if "/shapley" in ruta:
            return self._shapley(rbd, (parametros or {}).get("factor", "EFECTIVR"))
        if ruta.endswith("/ranking"):
            return self._ranking(rbd)
        return self._prediccion(rbd)

    def enviar(self, ruta: str, cuerpo: dict[str, Any]) -> dict:
        self.llamadas.append((ruta, dict(cuerpo)))
        partes = [p for p in ruta.split("/") if p]
        rbd = partes[1] if len(partes) > 1 else ""
        self._exigir(rbd)

        variables = cuerpo.get("variables", {}) or {}
        for nombre in variables:
            if nombre not in VARIABLES_SIMULABLES:
                raise ParametroInvalido(f"La variable '{nombre}' no es simulable.")
        for nombre, valor in variables.items():
            if nombre.startswith("simce") and not 100 <= float(valor) <= 400:
                raise ParametroInvalido(
                    f"El valor {valor} de '{nombre}' esta fuera del rango 100-400."
                )
            if nombre == "matricula_total" and float(valor) <= 0:
                raise ParametroInvalido("La matricula no puede ser cero ni negativa.")
        base = self._prediccion(rbd)
        base["indice"] = round(base["indice"] + 0.42 * len(variables), 2)
        return base

    # --- reglas de acceso -------------------------------------------------

    def _exigir(self, rbd: str) -> None:
        if rbd == RBD_AJENO or rbd not in self.jurisdiccion:
            raise FueraDeJurisdiccion(
                f"El RBD {rbd} no pertenece a la jurisdiccion del usuario."
            )
        if rbd == RBD_DEPURADO:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin registros en la base analitica.")
        if rbd == RBD_SIN_ARTEFACTO:
            raise ServicioNoDisponible("El artefacto del motor desagregado no esta disponible.")

    # --- cargas -----------------------------------------------------------

    @staticmethod
    def _prediccion(rbd: str) -> dict:
        factores = [dict(f) for f in FACTORES]
        if rbd == SIN_MEDICION_2M:
            factores[1]["valor"] = 51.30
            factores[1]["aporte_al_indice"] = 14.36
        return {
            "rbd": rbd,
            "indice": 67.60,
            "factores": factores,
            "estrategia": "desagregada",
            "version_modelo": "1.0.0",
            "incertidumbre_mae": 2.31,
            "advertencia": (
                "Estimacion referencial. Cinco de los seis factores estan acotados por "
                "informacion no publicada."
            ),
        }

    @staticmethod
    def _alertas(rbd: str) -> list[dict]:
        if rbd == TRAMO_100:
            return []
        return [
            {
                "tipo": "trampa_superacion",
                "severidad": "alta",
                "titulo": "Superacion estancada respecto del ciclo anterior",
                "detalle": "El factor Superacion premia el progreso, no la permanencia.",
            },
            {
                "tipo": "riesgo_normativo",
                "severidad": "media",
                "titulo": "Procesos administrativos sin resolver",
                "detalle": "Los procesos con sancion afectan Igualdad de Oportunidades.",
            },
        ]

    @staticmethod
    def _ranking(rbd: str) -> dict:
        return {
            "rbd": rbd,
            "ciclo": "2024-2025",
            "cluster_codigo": 12 if rbd != CAMBIA_CLUSTER else 27,
            "indicer": 67.60,
            "posicion_en_grupo": 41,
            "n_grupo": 118,
            "percentil": 65.30,
            "sel": 1 if rbd == TRAMO_100 else 3,
        }

    @staticmethod
    def _shapley(rbd: str, factor: str) -> dict:
        contribuciones = [
            {"variable": "simce_mat_4b", "etiqueta": "SIMCE Matematica 4 basico",
             "valor": 271.30, "contribucion": 4.21, "direccion": "sube"},
            {"variable": "simce_leng_4b", "etiqueta": "SIMCE Lectura 4 basico",
             "valor": 264.80, "contribucion": 2.65, "direccion": "sube"},
            {"variable": "tasa_aprobacion", "etiqueta": "Tasa de aprobacion",
             "valor": 96.40, "contribucion": 0.94, "direccion": "sube"},
            {"variable": "procesos_con_sancion", "etiqueta": "Procesos con sancion",
             "valor": 2.00, "contribucion": -1.20, "direccion": "baja"},
        ]
        if rbd == SIN_MEDICION_2M:
            contribuciones.append({
                "variable": "falta_simce_2m", "etiqueta": "Sin medicion de SIMCE 2 medio",
                "valor": None, "contribucion": -0.72, "direccion": "baja",
            })
        return {
            "rbd": rbd,
            "factor": factor,
            "prediccion": 71.20,
            "valor_base": 64.12,
            "aditividad_verificada": True,
            "contribuciones": contribuciones,
            "lectura": "Descomposicion local del factor mediante valores de Shapley.",
        }
