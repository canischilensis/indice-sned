"""Pruebas de cargabilidad del cuanto 3, sin dependencias nuevas.

## Que verifica

**RNF-13**: el servicio sostiene 20 usuarios concurrentes sobre las rutas de
lectura con **p95 <= 1.000 ms** y **tasa de error 0,0 %**.

## Tres escenarios

  LT-01  Carga nominal      · 20 usuarios, 60 segundos. Tiene criterio de aprobacion.
  LT-02  Carga sostenida    · 20 usuarios, 10 minutos, informado por ventanas de 2.
  LT-03  Punto de quiebre   · rampa creciente hasta superar el 1 % de error.

**LT-03 no aprueba ni reprueba nada.** Su proposito es caracterizar el techo del
sistema, no verificar un umbral. Un escenario cuyo resultado no puede reprobar la
prueba se declara como tal para no confundirlo con una verificacion.

## Por que httpx y asyncio y no una herramienta de carga

Ambas ya son dependencias del proyecto. Incorporar Locust, k6 o JMeter agregaria
una dependencia de infraestructura completa para producir una sola medicion, y el
volumen declarado en RNF-13 —veinte usuarios— no lo justifica. La contencion de
dependencias es una decision que este proyecto aplico en todas las demas
fronteras y no hay razon para abandonarla aqui.

## Disciplina de la medicion

**Calentamiento aparte.** Una pasada por ruta antes de medir, cuyos tiempos se
guardan en su propia seccion y **no entran en las tablas**. Sin esto, la primera
peticion a la ruta de explicabilidad cargaria un artefacto de 60 MB y ese costo
—que se paga una vez por proceso— se leeria como latencia de operacion.

**Percentiles, no promedio.** Un promedio de 400 ms es compatible con que una de
cada veinte peticiones tarde ocho segundos, y es esa peticion la que el usuario
recuerda.

**Se rota entre los tres RBD autorizados** para no medir siempre contra el mismo
valor ya resuelto en cache.

**El entorno se registra.** Una cifra de rendimiento sin la maquina que la
produjo no es reproducible y por lo tanto no es una medicion.

## Uso

    python -m uvicorn q3_servicio.main:app --app-dir quanta --port 8000   # sin --reload
    python tests/carga/guion_carga.py                 # los tres escenarios
    python tests/carga/guion_carga.py --escenario LT-01
    python tests/carga/guion_carga.py --escenario LT-03 --rampa 10,20,40,80,160

`--reload` se omite a proposito: el recargador interpone un supervisor que
distorsiona la latencia medida.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[2]
RESULTADOS = Path(__file__).resolve().parent / "resultados"

BASE = "http://127.0.0.1:8000/api/v1"
USUARIO, CLAVE = "sostenedor.demo", "demo"
RBDS = ("25520", "9012", "10156")

UMBRAL_P95_MS = 1000.0
UMBRAL_ERROR = 0.0
USUARIOS_NOMINAL = 20


def _rutas(rbd: str) -> list[tuple[str, str, str, dict | None]]:
    """(identificador estable, metodo, ruta, cuerpo) para un RBD dado.

    El identificador no lleva el RBD porque las cinco rutas se agregan entre los
    tres establecimientos: lo que se mide es la ruta, no el establecimiento.
    """
    return [
        ("GET /establecimientos", "GET", "/establecimientos", None),
        ("GET /prediccion/{rbd}", "GET", f"/prediccion/{rbd}", None),
        ("GET /xai/{rbd}/shapley", "GET", f"/xai/{rbd}/shapley", None),
        ("GET /establecimientos/{rbd}/ranking", "GET", f"/establecimientos/{rbd}/ranking", None),
        (
            "POST /prediccion/{rbd}/escenario",
            "POST",
            f"/prediccion/{rbd}/escenario",
            # Una variable de gestion dentro de rango. El constructor de
            # escenarios del dominio rechaza cualquier valor fuera del admisible,
            # de modo que un cuerpo invalido se veria como 422 y no como latencia.
            {"variables": {"simce_mate_4b": 285.0}},
        ),
    ]


# --- entorno ----------------------------------------------------------------


def _memoria_total_gb() -> str:
    try:
        import psutil

        return f"{psutil.virtual_memory().total / 1024**3:.1f} GB"
    except Exception:
        return "no determinada"


def _version_evaluada() -> str:
    try:
        salida = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=RAIZ, capture_output=True, text=True, timeout=10,
        )
        return salida.stdout.strip() or "no determinada"
    except Exception:
        return "no determinada"


async def _describir_entorno(cliente: httpx.AsyncClient) -> dict:
    """Que maquina, que backend de datos y que version del sistema se midio."""
    backend = os.getenv("REPOSITORIO_DATOS", "predeterminado del servicio")
    origen_declarado = None
    try:
        r = await cliente.get(f"{BASE}/salud", timeout=30)
        if r.status_code == 200:
            cuerpo = r.json()
            origen_declarado = cuerpo.get("origen") or cuerpo.get("repositorio")
    except Exception:
        pass

    return {
        "procesador": platform.processor() or platform.machine(),
        "nucleos_logicos": os.cpu_count(),
        "memoria_total": _memoria_total_gb(),
        "sistema_operativo": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "backend_datos_variable_entorno": backend,
        "backend_datos_declarado_por_el_servicio": origen_declarado,
        "base_en_la_misma_maquina": "si" if backend != "postgres" else "por confirmar",
        "version_evaluada": _version_evaluada(),
        "fecha_hora_inicio": datetime.now().isoformat(timespec="seconds"),
    }


# --- medicion ---------------------------------------------------------------


async def _autenticar(cliente: httpx.AsyncClient) -> str:
    r = await cliente.post(
        f"{BASE}/auth/token",
        data={"username": USUARIO, "password": CLAVE},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def _una(cliente, cabeceras, metodo, ruta, cuerpo) -> tuple[float, int, str | None]:
    inicio = time.perf_counter()
    try:
        if metodo == "GET":
            r = await cliente.get(f"{BASE}{ruta}", headers=cabeceras, timeout=60)
        else:
            r = await cliente.post(f"{BASE}{ruta}", headers=cabeceras, json=cuerpo, timeout=60)
        ms = (time.perf_counter() - inicio) * 1000
        # El cuerpo del error se conserva recortado: un 503 sin motivo obliga a
        # repetir la corrida completa para averiguar por que fallo.
        detalle = None if r.status_code < 400 else (r.text or "")[:200]
        return ms, r.status_code, detalle
    except Exception as exc:
        ms = (time.perf_counter() - inicio) * 1000
        return ms, 0, f"{type(exc).__name__}: {exc}"[:200]


async def _calentar(cliente, cabeceras) -> list[dict]:
    """Una pasada por ruta. NO entra en las tablas."""
    print("Calentamiento (fuera de las tablas)")
    registro = []
    for etiqueta, metodo, ruta, cuerpo in _rutas(RBDS[0]):
        ms, codigo, detalle = await _una(cliente, cabeceras, metodo, ruta, cuerpo)
        registro.append({"ruta": etiqueta, "ms": round(ms, 1), "codigo": codigo, "detalle": detalle})
        print(f"  {etiqueta:<38} {ms:>9.1f} ms   HTTP {codigo}")
    print()
    return registro


async def _usuario(cliente, cabeceras, hasta: float, indice: int, muestras: list) -> None:
    """Un usuario virtual: recorre las cinco rutas en bucle hasta que se acabe el tiempo."""
    ciclo = indice
    while time.perf_counter() < hasta:
        rbd = RBDS[ciclo % len(RBDS)]
        for etiqueta, metodo, ruta, cuerpo in _rutas(rbd):
            if time.perf_counter() >= hasta:
                return
            marca = time.perf_counter()
            ms, codigo, detalle = await _una(cliente, cabeceras, metodo, ruta, cuerpo)
            muestras.append(
                {"ruta": etiqueta, "rbd": rbd, "ms": ms, "codigo": codigo,
                 "detalle": detalle, "t": marca}
            )
        ciclo += 1


async def _correr(cliente, cabeceras, usuarios: int, segundos: float) -> list[dict]:
    muestras: list[dict] = []
    inicio = time.perf_counter()
    hasta = inicio + segundos
    await asyncio.gather(
        *(_usuario(cliente, cabeceras, hasta, i, muestras) for i in range(usuarios))
    )
    for m in muestras:
        m["t"] = m["t"] - inicio
    return muestras


def _percentil(valores: list[float], p: float) -> float:
    if not valores:
        return float("nan")
    orden = sorted(valores)
    k = max(0, min(len(orden) - 1, int(round(p * len(orden))) - 1))
    return orden[k]


def _resumir(muestras: list[dict], segundos: float) -> dict:
    """Agrega por ruta. La tasa de error se desglosa por codigo HTTP."""
    por_ruta: dict[str, dict] = {}
    for etiqueta in dict.fromkeys(m["ruta"] for m in muestras):
        propias = [m for m in muestras if m["ruta"] == etiqueta]
        tiempos = [m["ms"] for m in propias]
        fallidas = [m for m in propias if m["codigo"] >= 400 or m["codigo"] == 0]
        codigos: dict[str, int] = {}
        for m in propias:
            clave = str(m["codigo"]) if m["codigo"] else "sin respuesta"
            codigos[clave] = codigos.get(clave, 0) + 1
        p95 = _percentil(tiempos, 0.95)
        por_ruta[etiqueta] = {
            "peticiones": len(propias),
            "p50_ms": round(_percentil(tiempos, 0.50), 1),
            "p95_ms": round(p95, 1),
            "p99_ms": round(_percentil(tiempos, 0.99), 1),
            "max_ms": round(max(tiempos), 1) if tiempos else None,
            "media_ms": round(statistics.mean(tiempos), 1) if tiempos else None,
            "errores": len(fallidas),
            "tasa_error": round(len(fallidas) / len(propias), 4) if propias else 0.0,
            "codigos_http": codigos,
            "peticiones_por_segundo": round(len(propias) / segundos, 2) if segundos else None,
            "cumple_rnf13": bool(p95 <= UMBRAL_P95_MS and not fallidas),
            "ejemplos_de_error": [m["detalle"] for m in fallidas[:3] if m["detalle"]],
        }

    tiempos = [m["ms"] for m in muestras]
    fallidas = [m for m in muestras if m["codigo"] >= 400 or m["codigo"] == 0]
    return {
        "por_ruta": por_ruta,
        "global": {
            "peticiones": len(muestras),
            "p50_ms": round(_percentil(tiempos, 0.50), 1) if tiempos else None,
            "p95_ms": round(_percentil(tiempos, 0.95), 1) if tiempos else None,
            "p99_ms": round(_percentil(tiempos, 0.99), 1) if tiempos else None,
            "max_ms": round(max(tiempos), 1) if tiempos else None,
            "errores": len(fallidas),
            "tasa_error": round(len(fallidas) / len(muestras), 4) if muestras else 0.0,
            "peticiones_por_segundo": round(len(muestras) / segundos, 2) if segundos else None,
        },
    }


def _ventanas(muestras: list[dict], tramos: list[tuple[int, int]]) -> list[dict]:
    salida = []
    for desde, hasta in tramos:
        propias = [m for m in muestras if desde * 60 <= m["t"] < hasta * 60]
        tiempos = [m["ms"] for m in propias]
        fallidas = [m for m in propias if m["codigo"] >= 400 or m["codigo"] == 0]
        salida.append({
            "intervalo": f"minutos {desde} a {hasta}",
            "peticiones": len(propias),
            "p95_ms": round(_percentil(tiempos, 0.95), 1) if tiempos else None,
            "errores": len(fallidas),
            "tasa_error": round(len(fallidas) / len(propias), 4) if propias else 0.0,
        })
    return salida


def _guardar(nombre: str, contenido: dict) -> Path:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RESULTADOS / f"{nombre}_{sello}.json"
    destino.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Salida cruda: {destino.relative_to(RAIZ)}")
    return destino


# --- escenarios -------------------------------------------------------------


async def lt01(cliente, cabeceras, entorno) -> dict:
    print(f"LT-01 · carga nominal · {USUARIOS_NOMINAL} usuarios, 60 s")
    muestras = await _correr(cliente, cabeceras, USUARIOS_NOMINAL, 60)
    resumen = _resumir(muestras, 60)
    for etiqueta, d in resumen["por_ruta"].items():
        marca = "cumple" if d["cumple_rnf13"] else "INCUMPLE"
        print(f"  {etiqueta:<38} n={d['peticiones']:>5}  p95={d['p95_ms']:>9.1f} ms  "
              f"err={d['errores']:>3}  {marca}")
    _guardar("LT-01_nominal", {"escenario": "LT-01", "entorno": entorno,
                               "usuarios": USUARIOS_NOMINAL, "segundos": 60, **resumen})
    return resumen


async def lt02(cliente, cabeceras, entorno) -> dict:
    print(f"\nLT-02 · carga sostenida · {USUARIOS_NOMINAL} usuarios, 10 min")
    print("  (esto tarda diez minutos; se informa al terminar)")
    muestras = await _correr(cliente, cabeceras, USUARIOS_NOMINAL, 600)
    resumen = _resumir(muestras, 600)
    resumen["ventanas"] = _ventanas(muestras, [(0, 2), (4, 6), (8, 10)])
    for v in resumen["ventanas"]:
        print(f"  {v['intervalo']:<20} n={v['peticiones']:>6}  p95={v['p95_ms']} ms  err={v['errores']}")
    _guardar("LT-02_sostenida", {"escenario": "LT-02", "entorno": entorno,
                                 "usuarios": USUARIOS_NOMINAL, "segundos": 600, **resumen})
    return resumen


async def lt03(cliente, cabeceras, entorno, rampa: list[int]) -> dict:
    print("\nLT-03 · punto de quiebre · rampa creciente")
    print("  Sin criterio de aprobacion: caracteriza el techo, no verifica un umbral.\n")
    niveles = []
    quiebre = None
    for usuarios in rampa:
        muestras = await _correr(cliente, cabeceras, usuarios, 30)
        r = _resumir(muestras, 30)["global"]
        niveles.append({"usuarios": usuarios, **r})
        print(f"  {usuarios:>4} usuarios  {r['peticiones_por_segundo']:>8.2f} pet/s  "
              f"p95={r['p95_ms']:>9.1f} ms  error={r['tasa_error']:.2%}")
        if r["tasa_error"] > 0.01:
            quiebre = usuarios
            print(f"\n  Punto de quiebre: {usuarios} usuarios concurrentes "
                  f"(tasa de error {r['tasa_error']:.2%} > 1 %)")
            break
    if quiebre is None:
        print(f"\n  No se alcanzo el quiebre hasta {rampa[-1]} usuarios. "
              "El techo esta por encima de la rampa probada.")
    salida = {"escenario": "LT-03", "entorno": entorno, "rampa": rampa,
              "segundos_por_nivel": 30, "niveles": niveles, "punto_de_quiebre": quiebre}
    _guardar("LT-03_quiebre", salida)
    return salida


async def principal(argv=None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--escenario", choices=["LT-01", "LT-02", "LT-03", "todos"], default="todos")
    analizador.add_argument("--rampa", default="10,20,40,80,160",
                            help="Niveles de la rampa de LT-03, separados por coma")
    args = analizador.parse_args(argv)

    print("=" * 74)
    print("Pruebas de cargabilidad · RNF-13: p95 <= 1.000 ms y 0,0 % de error con 20 usuarios")
    print("=" * 74 + "\n")

    limites = httpx.Limits(max_connections=400, max_keepalive_connections=100)
    async with httpx.AsyncClient(limits=limites) as cliente:
        try:
            token = await _autenticar(cliente)
        except Exception as exc:
            print(f"No se pudo autenticar contra {BASE}: {exc}")
            print("Levanta el servicio antes de medir:")
            print("  python -m uvicorn q3_servicio.main:app --app-dir quanta --port 8000")
            return 1
        cabeceras = {"Authorization": f"Bearer {token}"}

        entorno = await _describir_entorno(cliente)
        print("Entorno de ejecucion")
        for k, v in entorno.items():
            print(f"  {k:<42} {v}")
        print()

        entorno["calentamiento"] = await _calentar(cliente, cabeceras)

        if args.escenario in ("LT-01", "todos"):
            await lt01(cliente, cabeceras, entorno)
        if args.escenario in ("LT-02", "todos"):
            await lt02(cliente, cabeceras, entorno)
        if args.escenario in ("LT-03", "todos"):
            await lt03(cliente, cabeceras, entorno, [int(x) for x in args.rampa.split(",")])

    print("\nMedicion terminada. Los JSON de "
          f"{RESULTADOS.relative_to(RAIZ)} son la evidencia; las tablas se arman desde ahi.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(principal()))
