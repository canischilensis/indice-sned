"""Adaptador de produccion: consulta las vistas de PostgreSQL.

Usa `ml.mv_matriz_entrenamiento` (representacion ancha que exigen los
algoritmos) y `hechos.v_ranking_intra_cluster` (posicion relativa dentro del
grupo homogeneo, que es la mecanica efectiva de seleccion del beneficio).

Nota sobre el RBD: en el esquema fisico es INTEGER, su forma canonica. La
ingesta lo lee como texto para no perder ceros a la izquierda durante el
parseo; aqui ya llega normalizado y se convierte al consultar.
"""

from __future__ import annotations

from q3_servicio.repositorios.contrato import (
    ConjuntoNoDisponible,
    EstablecimientoNoEncontrado,
    RepositorioEstablecimientos,
)

CONSULTA_DETALLE = """
    SELECT m.*, r.posicion_en_grupo, r.n_grupo, r.percentil, r.sel
    FROM ml.mv_matriz_entrenamiento m
    LEFT JOIN hechos.v_ranking_intra_cluster r
           ON r.rbd = m.rbd AND r.periodo_id = m.periodo_id
    WHERE m.rbd = :rbd
      AND (:bienio IS NULL OR m.bienio_premio = :bienio)
    ORDER BY m.periodo_id DESC
    LIMIT 1
"""

CONSULTA_LISTADO = """
    SELECT rbd, bienio_premio, cluster_codigo, indicer
    FROM ml.mv_matriz_entrenamiento
    WHERE rbd = ANY(:rbds)
    ORDER BY rbd, periodo_id DESC
    LIMIT :limite
"""

CONSULTA_COLUMNAS = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'ml' AND table_name = 'mv_matriz_entrenamiento'
"""


class RepositorioPostgres(RepositorioEstablecimientos):
    origen = "postgres"

    def __init__(self, url: str | None = None) -> None:
        self._url = url
        self._motor = None

    def _conectar(self):
        if self._motor is None:
            try:
                from sqlalchemy import create_engine
            except ImportError as exc:  # pragma: no cover
                raise ConjuntoNoDisponible("SQLAlchemy no esta instalado.") from exc

            from q3_servicio.core.config import config

            self._motor = create_engine(self._url or config().database_url, future=True)
        return self._motor

    @staticmethod
    def _como_entero(rbd: str) -> int:
        """El RBD viaja como texto por la aplicacion y es INTEGER en el esquema."""
        try:
            return int(str(rbd).strip().lstrip("0") or "0")
        except ValueError as exc:
            raise EstablecimientoNoEncontrado(f"RBD no numerico: {rbd!r}") from exc

    def obtener(self, rbd: str, periodo: str | None = None) -> dict:
        from sqlalchemy import text

        with self._conectar().connect() as cx:
            fila = cx.execute(
                text(CONSULTA_DETALLE), {"rbd": self._como_entero(rbd), "bienio": periodo}
            ).mappings().first()
        if fila is None:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin registros en la base analitica.")
        return dict(fila)

    def listar(self, rbds: list[str], limite: int = 50) -> list[dict]:
        from sqlalchemy import text

        with self._conectar().connect() as cx:
            filas = cx.execute(
                text(CONSULTA_LISTADO),
                {"rbds": [self._como_entero(r) for r in rbds], "limite": limite},
            ).mappings().all()
        return [dict(f) for f in filas]

    def variables_disponibles(self) -> set[str]:
        """Columnas de la vista materializada, para el diagnostico de cobertura."""
        from sqlalchemy import text

        try:
            with self._conectar().connect() as cx:
                return {f[0] for f in cx.execute(text(CONSULTA_COLUMNAS)).all()}
        except Exception:
            return set()

    def existe(self, rbd: str) -> bool:
        try:
            self.obtener(rbd)
            return True
        except EstablecimientoNoEncontrado:
            return False
