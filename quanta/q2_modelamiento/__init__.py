"""Cuanto 2 — Motor de modelamiento predictivo.

Frontera arquitectonica: nada fuera de este paquete conoce a scikit-learn,
TensorFlow ni el formato de serializacion de los artefactos. El resto del
sistema consume unicamente `EstrategiaPredictiva` (Patron Strategy).

Patrones implementados en este cuanto:
  Strategy        contrato.EstrategiaPredictiva
  Decorator       decoradores.EstrategiaAuditada / EstrategiaConCache
  Factory Method  fabrica.FabricaDeEstrategias
  Registry        registro_modelos.RegistroDeModelos
  Virtual Proxy   artefactos.ArtefactoDiferido
  Builder         escenario.ConstructorDeEscenario
"""

from q2_modelamiento.artefactos import ArtefactoDiferido, ArtefactoNoDisponible
from q2_modelamiento.contrato import (
    ContribucionVariable,
    CurvaSensibilidad,
    EstrategiaPredictiva,
    ExplicacionLocal,
    Prediccion,
)
from q2_modelamiento.decoradores import EstrategiaAuditada, EstrategiaConCache
from q2_modelamiento.escenario import ConstructorDeEscenario, Escenario, VariableNoSimulable
from q2_modelamiento.fabrica import (
    FabricaDeEstrategias,
    estrategias_disponibles,
    fabrica,
    obtener_estrategia,
)
from q2_modelamiento.registro_modelos import RegistroDeModelos, registro

__all__ = [
    "EstrategiaPredictiva",
    "Prediccion",
    "ExplicacionLocal",
    "ContribucionVariable",
    "CurvaSensibilidad",
    "EstrategiaAuditada",
    "EstrategiaConCache",
    "ConstructorDeEscenario",
    "Escenario",
    "VariableNoSimulable",
    "FabricaDeEstrategias",
    "fabrica",
    "obtener_estrategia",
    "estrategias_disponibles",
    "RegistroDeModelos",
    "registro",
    "ArtefactoDiferido",
    "ArtefactoNoDisponible",
]
