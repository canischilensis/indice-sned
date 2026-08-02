"""Virtual Proxy / Lazy Load sobre los artefactos serializados.

Gamma et al. (1994) describen el proxy virtual como aquel que "crea objetos
costosos bajo demanda". Fowler (2002) lo formaliza como Lazy Load: "un objeto
que no contiene todos los datos que necesitas, pero sabe como obtenerlos".

Aqui la fuerza es concreta: el registro pesa 220 MB repartidos en nueve
artefactos, y una peticion tipica usa uno o dos. Cargarlos al arrancar la API
costaria cientos de MB y varios segundos de arranque para nada.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class ArtefactoNoDisponible(RuntimeError):
    """El artefacto serializado no esta en el registro local."""


class ArtefactoDiferido:
    """Sustituto de un modelo entrenado. Materializa la deserializacion en el
    primer uso y registra el costo de esa carga."""

    def __init__(self, ruta: Path, etiqueta: str = "") -> None:
        self._ruta = ruta
        self._etiqueta = etiqueta or ruta.stem
        self._real: Any | None = None
        self._segundos_de_carga: float | None = None

    # -- estado ------------------------------------------------------------

    @property
    def materializado(self) -> bool:
        return self._real is not None

    @property
    def segundos_de_carga(self) -> float | None:
        """Insumo del presupuesto de latencia del plan de pruebas."""
        return self._segundos_de_carga

    @property
    def megabytes(self) -> float:
        return round(self._ruta.stat().st_size / 1_048_576, 2) if self._ruta.exists() else 0.0

    # -- materializacion ---------------------------------------------------

    def materializar(self) -> Any:
        if self._real is not None:
            return self._real

        if not self._ruta.exists():
            raise ArtefactoNoDisponible(
                f"Falta el artefacto '{self._ruta.name}' en {self._ruta.parent}.\n"
                "Los .joblib/.keras NO se versionan en git (ver .gitignore). "
                "Reentrena el modelo o restaura el registro desde el respaldo."
            )

        inicio = time.perf_counter()
        if self._ruta.suffix == ".keras":
            from tensorflow import keras  # import diferido: solo si hay red neuronal

            self._real = keras.models.load_model(self._ruta)
        else:
            import joblib

            self._real = joblib.load(self._ruta)
        self._segundos_de_carga = round(time.perf_counter() - inicio, 3)
        return self._real

    # -- superficie del modelo real ---------------------------------------

    def predict(self, X):
        return self.materializar().predict(X)

    def __getattr__(self, nombre: str) -> Any:
        """Cualquier otro atributo se delega al objeto real, materializandolo."""
        if nombre.startswith("_"):
            raise AttributeError(nombre)
        return getattr(self.materializar(), nombre)

    def __repr__(self) -> str:
        estado = "materializado" if self.materializado else "diferido"
        return f"<ArtefactoDiferido {self._etiqueta} {self.megabytes} MB, {estado}>"
