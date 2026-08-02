# Notebooks — evidencia reproducible por fase

Los notebooks se movieron y renombraron siguiendo el **viaje del dato** del Visual Story
Mapping. Su contenido **no fue modificado**: son la evidencia de los Sprints tal como se
ejecutaron.

| Nuevo nombre | Nombre original | Fase / Sprint |
|--------------|-----------------|---------------|
| `01_ingesta/01_01_simce.ipynb` | `SIMCE.ipynb` | Ingesta (S1-S2) |
| `01_ingesta/01_02_idps.ipynb` | `IDPS.ipynb` | Ingesta |
| `01_ingesta/01_03_rendimiento.ipynb` | `RENDIMIENTO.ipynb` | Depuracion historica (S1) |
| `01_ingesta/01_04_matricula.ipynb` | `MATRICULA.ipynb` | Ingesta |
| `01_ingesta/01_05_sep.ipynb` | `SEP.ipynb` | Ingesta |
| `01_ingesta/01_06_ive.ipynb` | `IVE.ipynb` | Ingesta |
| `01_ingesta/01_07_procesos_administrativos.ipynb` | `PAT.ipynb` | Ingesta |
| `01_ingesta/01_08_personal_colaboradores.ipynb` | `COLABORADORES.ipynb` | Ingesta |
| `01_ingesta/01_09_denuncias.ipynb` | `DENUNCIAS.ipynb` | Ingesta |
| `01_ingesta/01_10_mediaciones.ipynb` | `MEDIACIONES.ipynb` | Ingesta |
| `02_integracion/02_01_sned_maestro_ciclos.ipynb` | `SNED.ipynb` | Integracion y llave RBD+anio (S2) |
| `03_features/03_01_correccion_unidad_analisis.ipynb` | `MODELAMIENTO-2.ipynb` | Feature engineering (S3) |
| `04_modelamiento/04_01_motor_desagregado_por_factor.ipynb` | `MOTOR-SIMULADOR.ipynb` | Modelamiento + XAI (S4) |
| `04_modelamiento/04_02_benchmark_arquitecturas_global.ipynb` | `BENCHMARK_GLOBAL.ipynb` | Comparacion de arquitecturas (S4) |

---

## ATENCION — rutas relativas

Los notebooks fueron escritos cuando todo colgaba de una sola carpeta, con rutas del tipo
`SIMCE/simce4b2024_rbd_final.xlsx` o `PROCESADOS/tabla_modelo_final.parquet`.
Tras la reorganizacion, esos destinos son:

| Ruta antigua | Ruta nueva |
|--------------|------------|
| `SIMCE/` , `IDPS/` , `MATRICULA/` ... | `../../data/raw/simce/` , `../../data/raw/idps/` ... |
| `PROCESADOS/` | `../../data/processed/` |
| `MODELOS/*.joblib` | `../../models/registry/` |
| `MODELOS/*.json` | `../../models/metadata/` |

**Los notebooks no correran tal cual hasta actualizar esas rutas.** Se conservaron intactos
de forma deliberada: son la evidencia validada de los Sprints y el codigo no debia tocarse.

Forma recomendada de arreglarlo (una sola celda al inicio de cada notebook):

```python
import sys, os
from pathlib import Path
RAIZ = Path.cwd().parents[1]              # sube desde notebooks/<fase>/
sys.path.insert(0, str(RAIZ / "quanta"))
os.chdir(RAIZ)                            # las rutas relativas pasan a colgar de la raiz

RAW       = RAIZ / "data" / "raw"
PROCESADO = RAIZ / "data" / "processed"
REGISTRO  = RAIZ / "models" / "registry"
METADATOS = RAIZ / "models" / "metadata"
```

y luego reemplazar `"SIMCE/..."` por `RAW / "simce" / "..."`.

Alternativa sin editar rutas: usar el modulo central ya disponible,
`from q2_modelamiento.rutas import DATA_RAW, DATA_PROCESSED, MODEL_REGISTRY`.

## Kernel

`setup.ps1` y `make init` registran el kernel **indice-sned** ligado al entorno virtual.
Seleccionalo en Jupyter antes de ejecutar cualquier notebook.
