"""Adaptador de desarrollo: lee el parquet producido por el cuanto 1.

Permite que el prototipo funcione sin PostgreSQL levantado, que es la condicion
para demostrarlo en una defensa sin depender de Docker.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from compartido.rutas import DATA_PROCESSED
from q3_servicio.repositorios.contrato import (
    ConjuntoNoDisponible,
    EstablecimientoNoEncontrado,
    RepositorioEstablecimientos,
)

# Orden deliberado: primero la tabla que reproduce la representacion de
# entrenamiento (23.111 observaciones, la misma cifra que declara
# metadatos_modelo_global.json). Las restantes son respaldos historicos con
# menos variables y sirven solo para que el prototipo no quede inoperante.
# Las once columnas de eventos SIE. El merge original fue LEFT y dejo nulos
# donde no hubo evento; un establecimiento sin denuncias registradas tiene CERO
# denuncias, no un dato desconocido. La base ya carga 0 desde los parquet
# originales, de modo que aqui se normaliza para que ambos adaptadores
# devuelvan lo mismo.
EVENTOS_SIE = (
    "denuncias_total", "denuncias_fiscalizacion", "denuncias_juridica",
    "denuncias_ciberbullying", "procesos_total", "procesos_con_sancion",
    "procesos_multa", "procesos_privacion_subvencion",
    "mediaciones_total", "mediaciones_efectivas", "mediaciones_de_denuncia",
)

CANDIDATOS = (
    # Preferida cuando existe: es la tabla analitica con los ciclos posteriores
    # incorporados. Si se borra, el sistema vuelve al comportamiento anterior
    # sin tocar una linea de codigo, que es la razon de resolverlo por orden de
    # candidatos y no por configuracion.
    "tabla_modelo_ciclos.parquet",
    "tabla_modelo_largo.parquet",
    "tabla_modelo_final.parquet",
    "tabla_entrenamiento_completa.parquet",
    "tabla_entrenamiento_modelo.parquet",
)


def _texto(v):
    return None if v is None or pd.isna(v) else str(v)


def _entero(v):
    return None if v is None or pd.isna(v) else int(float(v))


def _decimal(v):
    return None if v is None or pd.isna(v) else round(float(v), 3)


class RepositorioParquet(RepositorioEstablecimientos):
    origen = "parquet"

    def __init__(self, carpeta=None, candidatos: tuple[str, ...] = CANDIDATOS) -> None:
        self._carpeta = carpeta or DATA_PROCESSED
        self._candidatos = candidatos

    @lru_cache(maxsize=4)  # noqa: B019 - instancia unica por proceso
    def _conjunto(self) -> pd.DataFrame:
        for nombre in self._candidatos:
            ruta = self._carpeta / nombre
            if ruta.exists():
                df = pd.read_parquet(ruta)
                for col in df.columns:
                    if col.lower() == "rbd":
                        df["rbd"] = df[col].astype("string").str.strip()
                        break
                for c in EVENTOS_SIE:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
                if "cod_depe2" in df.columns:
                    # Sin traduccion de codigos: la diferencia con PostgreSQL es
                    # temporal, no de vocabulario. Ver la nota en la prueba de
                    # paridad.
                    df["cod_depe2"] = pd.to_numeric(df["cod_depe2"], errors="coerce")
                return df
        raise ConjuntoNoDisponible(
            f"No se encontro ningun conjunto en {self._carpeta}. "
            "Ejecuta los notebooks 01_ y 02_ o restaura data/processed."
        )

    @lru_cache(maxsize=2)  # noqa: B019 - instancia unica por proceso
    def _maestro(self):
        """Resultados oficiales del SNED, todos los ciclos publicados.

        Es una fuente COMPLEMENTARIA y no reemplaza al conjunto analitico. La
        distincion importa: el conjunto analitico trae las variables que el
        modelo necesita para estimar, y llega hasta donde llegue el ultimo
        procesamiento de rasgos. El maestro trae el resultado ya publicado por
        el organismo, y puede ir un ciclo por delante.

        Mezclarlos en una sola tabla obligaria a reprocesar toda la matriz de
        entrenamiento cada vez que se publica un ciclo nuevo, solo para poder
        mostrar una cifra que no alimenta al modelo. Se leen aparte y cada uno
        responde lo suyo: el analitico estima, el maestro informa.

        Si el archivo no existe, se devuelve None y todo sigue funcionando con
        el conjunto analitico, como antes.
        """
        ruta = self._carpeta / "sned_maestro_ciclos.parquet"
        if not ruta.exists():
            return None
        df = pd.read_parquet(ruta)
        for col in df.columns:
            if col.lower() == "rbd":
                df["rbd"] = df[col].astype("string").str.strip()
                break
        return df

    def _ultimo_ciclo_oficial(self, rbd: str) -> dict | None:
        """Fila del ciclo publicado mas reciente para este establecimiento."""
        maestro = self._maestro()
        if maestro is None or "BIENIO_PREMIO" not in maestro.columns:
            return None
        filas = maestro[maestro["rbd"] == str(rbd).strip()]
        filas = filas[filas["INDICER"].notna()] if "INDICER" in filas.columns else filas
        if filas.empty:
            return None
        fila = filas.sort_values("BIENIO_PREMIO").iloc[-1]
        return {k: (None if pd.isna(v) else v) for k, v in fila.to_dict().items()}

    def obtener(self, rbd: str, periodo: str | None = None) -> dict:
        df = self._conjunto()
        filas = df[df["rbd"] == str(rbd).strip()]
        if filas.empty:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin registros en el conjunto analitico.")
        if periodo and "BIENIO_PREMIO" in filas.columns:
            candidatas = filas[filas["BIENIO_PREMIO"].astype("string") == periodo]
            if not candidatas.empty:
                filas = candidatas
        fila = filas.iloc[-1]
        return {k: (None if pd.isna(v) else v) for k, v in fila.to_dict().items()}

    def listar(self, rbds: list[str], limite: int = 50) -> list[dict]:
        """Un registro por establecimiento, el del ciclo mas reciente.

        La nomenclatura de salida es la del contrato `ResumenEstablecimiento`,
        no la de las columnas del parquet: el adaptador traduce, el servicio no
        deberia saber que el origen usa mayusculas.
        """
        df = self._conjunto()
        subset = df[df["rbd"].isin([str(r) for r in rbds])]
        if subset.empty:
            return []
        if "BIENIO_PREMIO" in subset.columns:
            subset = subset.sort_values("BIENIO_PREMIO").drop_duplicates("rbd", keep="last")
        salida = []
        for _, fila in subset.head(limite).iterrows():
            rbd = str(fila["rbd"])
            # El resultado publicado manda sobre el del conjunto analitico: si el
            # organismo ya publico un ciclo posterior, es ese el que el directivo
            # tiene enfrente cuando abre el sistema.
            oficial = self._ultimo_ciclo_oficial(rbd) or {}
            salida.append(
                {
                    "rbd": rbd,
                    "bienio_premio": _texto(oficial.get("BIENIO_PREMIO", fila.get("BIENIO_PREMIO"))),
                    "cluster_codigo": _entero(oficial.get("CLUSTER", fila.get("CLUSTER"))),
                    "indicer": _decimal(oficial.get("INDICER", fila.get("INDICER"))),
                }
            )
        return salida

    def variables_disponibles(self) -> set[str]:
        """Columnas efectivamente presentes en el conjunto activo."""
        try:
            return set(self._conjunto().columns)
        except ConjuntoNoDisponible:
            return set()

    def existe(self, rbd: str) -> bool:
        try:
            return not self._conjunto()[self._conjunto()["rbd"] == str(rbd).strip()].empty
        except ConjuntoNoDisponible:
            return False

    #: Cuantos lideres del grupo se devuelven. Cinco alcanzan para que el
    #: directivo reconozca contra quien compite sin convertir la respuesta en un
    #: listado que nadie lee.
    LIDERES = 5

    def ranking(self, rbd: str, periodo: str | None = None) -> dict:
        """Posicion dentro del grupo homogeneo, con el corte y los lideres.

        Se calcula sobre el maestro oficial cuando esta disponible, porque es la
        fuente que contiene el ciclo publicado mas reciente y los nombres de los
        establecimientos. Si no lo esta, se usa el conjunto analitico y el
        resultado es el mismo de antes.
        """
        maestro = self._maestro()
        oficial = self._ultimo_ciclo_oficial(rbd)
        if maestro is not None and oficial is not None and not periodo:
            df, fila = maestro, oficial
        else:
            df, fila = self._conjunto(), self.obtener(rbd, periodo)

        ciclo = fila.get("BIENIO_PREMIO")
        cluster = fila.get("CLUSTER")
        if ciclo is None or cluster is None or "INDICER" not in df.columns:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin ranking calculable.")

        grupo = df[(df["BIENIO_PREMIO"] == ciclo) & (df["CLUSTER"] == cluster)]
        grupo = grupo[grupo["INDICER"].notna()].sort_values("INDICER", ascending=False)
        orden = grupo["rbd"].tolist()
        n = len(orden)
        clave = str(rbd).strip()
        if clave not in orden:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin ranking calculable en {ciclo}.")
        pos = orden.index(clave) + 1

        lideres = [
            {
                "rbd": str(f["rbd"]),
                "nombre": _texto(f.get("NOM_RBD")) or f"RBD {f['rbd']}",
                "indicer": _decimal(f.get("INDICER")),
                "posicion": i,
                "es_consultado": str(f["rbd"]) == clave,
            }
            for i, (_, f) in enumerate(grupo.head(self.LIDERES).iterrows(), start=1)
        ]

        # Corte del ciclo: el indice mas bajo que si obtuvo el beneficio. No es
        # un umbral fijo —el SNED no los tiene— sino el resultado observado de
        # este grupo en este ciclo, y por eso viaja junto al ciclo que lo produjo.
        corte = None
        premiados = 0
        if "SEL" in grupo.columns:
            gana = grupo[pd.to_numeric(grupo["SEL"], errors="coerce").isin([1, 2])]
            premiados = int(len(gana))
            if premiados:
                corte = _decimal(gana["INDICER"].min())

        return {
            "rbd": clave,
            "ciclo": str(ciclo),
            "cluster_codigo": int(cluster),
            "indicer": float(fila["INDICER"]),
            "posicion_en_grupo": pos,
            "n_grupo": n,
            "percentil": round((n - pos) / (n - 1), 4) if n > 1 else 0.0,
            "sel": int(fila["SEL"]) if fila.get("SEL") is not None else None,
            "premiados_en_grupo": premiados,
            "corte_premiado": corte,
            "lideres": lideres,
        }
