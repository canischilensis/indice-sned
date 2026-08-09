# indice-sned

Ecosistema de analitica predictiva B2B con **Inteligencia Artificial Explicable (XAI)**
para la anticipacion del **Indice SNED** de establecimientos educacionales chilenos.

> La IA asiste; la decision estrategica y financiera la toma exclusivamente el equipo directivo.

---

## Objetivos del proyecto

**General.** Robustecer la planificacion estrategica de directivos y sostenedores escolares
mediante el desarrollo de un prototipo predictivo basado en XAI para la anticipacion del Indice SNED.

| OE | Objetivo | Donde vive en el repositorio | Estado |
|----|----------|------------------------------|--------|
| **1** | Integrar >= 8 fuentes publicas (2018-2025) con llave estricta RBD + anio, sin datos personales | `quanta/q1_ingesta/`, `notebooks/01_ingesta/`, `data/raw/` | Cumplido — 11 fuentes |
| **2** | Analizar y depurar registros historicos sin clasificacion previa, en formato largo | `quanta/q1_ingesta/calidad.py`, `notebooks/02_integracion/` | Cumplido — 23.111 obs. / 7.754 estab. |
| **3** | Construir >= 15 variables consumiendo los Grupos Homogeneos oficiales | `notebooks/03_features/` | Cumplido — 65 variables |
| **4** | Entrenar y comparar >= 3 arquitecturas con validacion cruzada agrupada | `quanta/q2_modelamiento/`, `notebooks/04_modelamiento/` | Cumplido — HistGB / MLP / RF |
| **5** | Desarrollar el prototipo B2B de 3 ventanas con XAI | `quanta/q3_servicio/`, `quanta/q4_cliente/` | **En curso** |

---

## Arquitectura: cuatro cuantos

El sistema se organiza en **Cuantos de Arquitectura** (Ford et al., 2021): unidades de alta
cohesion y despliegue independiente. Cada uno vive en `quanta/` y solo se comunica con los
demas a traves de contratos explicitos.

```
                data/raw (11 fuentes MINEDUC)
                          |
    +---------------------v----------------------+
    |  Q1  q1_ingesta                            |  ETL/ELT, MDM RBD+anio, cuarentena
    +---------------------|----------------------+
                data/processed (*.parquet)
                          |
    +---------------------v----------------------+
    |  Q2  q2_modelamiento                       |  Motor dual + SHAP/ICE + registro
    |      contrato.EstrategiaPredictiva  <----- FRONTERA STRATEGY
    +---------------------|----------------------+
                          |
    +---------------------v----------------------+
    |  Q3  q3_servicio (FastAPI)                 |  API + RBAC. NO importa sklearn.
    +---------------------|----------------------+
                       HTTP/JSON
    +---------------------v----------------------+
    |  Q4  q4_cliente (React + Vite)             |  Dashboard / Simulador / Reporte XAI
    +--------------------------------------------+
```

La frontera critica es `q2_modelamiento/contrato.py`. Cambiar de arboles a red neuronal,
o del motor desagregado al global, **no toca ninguna linea del cuanto 3 ni del 4**.
`scripts/verificar_arquitectura.py` convierte esa regla en una prueba ejecutable.

### El motor dual

| Motor | R2 | Proposito | Trazabilidad |
|-------|-----|-----------|--------------|
| **desagregado** (6 modelos, uno por factor + formula oficial) | 0,583 | Motor del simulador | variable -> factor -> indice |
| **global** (HistGradientBoosting, 65 variables) | 0,637 | Estimador de referencia | ninguna |

La diferencia de **0,054 puntos de R2 es el precio medido de la explicabilidad**.
Ambos se conservan porque responden preguntas distintas.

---

## Estructura del repositorio

```
indice-sned/
├── quanta/                     Los cuatro cuantos de arquitectura
│   ├── q1_ingesta/             Fuentes, calidad (CTRL-01), CLI
│   ├── q2_modelamiento/        Contrato Strategy, estrategias, XAI, registro, deriva
│   ├── q3_servicio/            FastAPI: routers, RBAC, esquemas Pydantic
│   ├── q4_cliente/             React + Vite: 3 ventanas funcionales
│   └── compartido/             Nucleo minimo comun (resolucion de rutas)
├── notebooks/                  Evidencia reproducible por fase del viaje del dato
├── data/                       raw / interim / processed / external   (git-ignorado)
├── models/                     registry (git-ignorado) + metadata (versionado)
├── db/                         DDL de los 4 esquemas + 3 vistas de consumo
├── contratos/                  Catalogo de factores: ponderaciones como DATO
├── docs/                       ARCHITECTURE.md, ADRs, informes de tesis
├── scripts/                    Inicializacion de BD y compuerta de arquitectura
└── tests/                      QA tridimensional: datos, modelo, API
```

---

## Puesta en marcha

### Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned   # una sola vez
.\setup.ps1
```

Reutiliza el entorno virtual existente (`env\`) o lo crea, instala dependencias,
registra el kernel de Jupyter, genera `.env` e instala el frontend si hay Node.

> **`env\` no es `.env`.** `env\` es la carpeta del entorno virtual;
> `.env` es el archivo de configuracion. Nombres parecidos, cosas distintas.

### Linux / macOS

```bash
make init
```

### Levantar el sistema

```powershell
# Terminal 1 — cuanto 3
.\env\Scripts\Activate.ps1
python -m uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000

# Terminal 2 — cuanto 4
cd quanta\q4_cliente
npm install          # solo la primera vez
npm run dev
```

- API y documentacion interactiva: <http://127.0.0.1:8000/docs>
- Interfaz B2B: <http://localhost:5173>
- Usuarios de demostracion: `directora.demo`, `sostenedor.demo`, `auditor.demo` — clave `demo`

### Base de datos

```bash
docker compose up -d postgres
python scripts/inicializar_bd.py     # 38 tablas en cuatro esquemas
python scripts/cargar_bd.py          # carga core, hechos y ml
```

**38 tablas**: `core` 16, `hechos` 6, `ml` 8, `app` 8. Las 15 primeras de `core` mas las 6 de
`hechos` derivan una a una del modelo entidad-relacion; la decimosexta,
`core.conjunto_entrenamiento`, es la lista maestra del conjunto depurado y no proviene del
diagrama. `ml` y `app` tampoco: son infraestructura de trazabilidad y de aplicacion.

El almacenamiento activo se elige por configuracion:

```
REPOSITORIO_DATOS=postgres   # predeterminado
REPOSITORIO_DATOS=parquet    # desarrollo y demostracion sin base levantada
```

Ambos adaptadores quedan operativos y conmutables. La paridad entre ellos esta verificada:
101 llamadas a 6 endpoints, cero divergencias (`tests/paridad/`).

---

## Compuerta de calidad

Ningun incremento se considera *Terminado* sin superar las tres barreras:

```bash
python scripts/verificar_arquitectura.py   # fronteras entre cuantos
pytest -m datos                            # QA-A: integridad de la llave y cuarentena
pytest -m modelo                           # QA-B: catalogo, anti-fuga, predictor trivial
pytest -m api                              # QA-C: RBAC y contratos HTTP
make qa                                    # todo lo anterior + lint
```

---

## Controles de arquitectura

| ID | Riesgo | Implementacion |
|----|--------|----------------|
| CTRL-01 | Orfandad de llaves | `q1_ingesta/calidad.py` — cuarentena con bandera de auditoria |
| CTRL-02 | Fuga de datos | `q2_modelamiento/validacion.py` — GroupKFold por RBD + exclusion de objetivos |
| CTRL-03 | Data drift | `q2_modelamiento/deriva.py` — linea base + verificacion bianual, decision humana |
| CTRL-04 | Acceso no autorizado | `q3_servicio/core/seguridad.py` — RBAC de minimo privilegio |
| CTRL-05 | Caja negra | `q2_modelamiento/registro_modelos.py` + esquema `modelos` en PostgreSQL |

---

## Que NO hace este proyecto

- **No hay MLOps.** Sin CI/CD, sin orquestacion, sin reentrenamiento continuo. El indice se
  calcula de forma bianual; una infraestructura de orquestacion seria, por si misma, deuda tecnica.
- **No replica el calculo estatal.** Cinco de los seis factores estan acotados por informacion
  que solo el organismo emisor posee (63 % de la ponderacion). Ver `contratos/catalogo_factores.json`.
- **No promete retorno.** El indice normaliza contra los extremos nacionales: una mejora realista
  de 15-20 puntos SIMCE aporta del orden de 0,5 puntos. La interfaz comunica direccion y
  sensibilidad, nunca garantia de acceso al beneficio.

---

## Lo que la conmutacion a PostgreSQL destapo

El ejercicio de paridad entre los dos adaptadores no solo verifico el patron Repository:
detecto un defecto que llevaba desde el inicio y que ninguna prueba anterior habia visto.

**El motor desagregado nunca habia podido predecir.** Los seis artefactos por factor fueron
entrenados con las variables base *mas* una bandera `<variable>_ausente` por cada una —
EFECTIVR espera 16 columnas, no 8; SUPERAR espera 30, no 16 — pero `metadatos_modelos.json`
declaraba solo las variables base. `EstrategiaDesagregada._matriz` construia la matriz desde
esa lista incompleta y scikit-learn rechazaba la llamada con
`ValueError: feature names should match`.

El defecto sobrevivio porque las 44 pruebas existentes ejercitaban el contrato, la fabrica y
los decoradores con dobles de prueba, nunca los artefactos reales. Solo al exigir que dos
adaptadores devolvieran lo mismo hubo que llamar al endpoint de prediccion de verdad, y ahi
aparecio.

La correccion fue tomar el orden de columnas de `feature_names_in_` del propio artefacto en
lugar de los metadatos, y completar `metadatos_modelos.json` con el vector real. La causa de
fondo eran los metadatos incompletos, no la estrategia.

## Limitaciones de rendimiento conocidas

Ambas estan medidas, tienen causa identificada y quedan sin resolver a proposito.

| Sintoma | Causa | Estado |
|---------|-------|--------|
| `POST /xai/simular` tarda **4,6 s** | 9 puntos de malla x 6 modelos = **54 inferencias** por llamada. El decorador de cache no ayuda porque cada punto es una observacion distinta. Ocurre en los dos adaptadores, asi que no depende del almacenamiento | Sin resolver |
| `GET /establecimientos/{rbd}/ranking` es **2,5x mas lento** en PostgreSQL (118 ms contra 47 ms) | `hechos.v_ranking_intra_cluster` recalcula `RANK()` y `PERCENT_RANK()` sobre las 54.298 filas en cada consulta. Se resolveria materializando la vista | Sin resolver |

## Documentacion

Indice maestro con todos los documentos y su correspondencia con el Capitulo IV de la tesis:
**`docs/README.md`**.

| Area | Documentos |
|------|-----------|
| Requisitos | `docs/requisitos/` — catalogo de requisitos, 12 casos de uso y matriz de trazabilidad |
| Arquitectura | `docs/arquitectura/` — arquitectura ad-hoc, vistas 4+1 y plataforma de operacion |
| | `docs/ARCHITECTURE.md` — documento vivo; `docs/PATRONES_DE_DISENO.md` — 12 patrones aplicados y 12 descartados |
| | `docs/adr/` — cinco decisiones de arquitectura registradas |
| Diseno | `docs/diseno/` — diseno del software, diseno de la base de datos y maquetas de pantalla |
| | `docs/diagramas/` — modelo de clases y diagramas de secuencia, en Mermaid y PNG |
| Gestion | `docs/gestion/` — metodologia y los cinco planes: calidad, cambios, comunicaciones, alcance y cronograma |
| Pruebas | `docs/planes/` — plan maestro mas los planes de integracion, aceptacion y compatibilidad |
| Manuales | `docs/manuales/` — instalacion, usuario, monitorizacion y nueve procedimientos operativos |
| Datos | `docs/FUENTES.md` — origen y re-descarga; `db/README.md` — que hace cada .sql |
| Cuadernos | `notebooks/README.md` — mapa por fase y advertencia de rutas |
