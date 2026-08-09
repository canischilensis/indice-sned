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

## Rutas: ahora salen del propio repositorio

Los cuadernos se escribieron en Google Colab y leian los datos desde Google Drive, con rutas del
tipo `/content/drive/MyDrive/.../SIMCE/`. **Eso ya no es asi.** Cada cuaderno abre con una celda
que resuelve la raiz del repositorio y define cuatro constantes:

```python
RAIZ            = _raiz_del_repositorio()          # busca pyproject.toml hacia arriba
RUTA_RAW        = <RAIZ>/data/raw/
RUTA_PROCESADOS = <RAIZ>/data/processed/
RUTA_REGISTRO   = <RAIZ>/models/registry/
RUTA_METADATOS  = <RAIZ>/models/metadata/
```

Correspondencia aplicada:

| Ruta de Drive | Destino en el repositorio |
|---------------|---------------------------|
| `SIMCE/`, `IDPS/`, `MATRICULA/`, `SEP/`, `IVE/`, `PAT/`, `PERSONAL/`, `DENUNCIAS/`, `MEDIACIONES/`, `RENDIMIENTO/`, `SNED/` | `data/raw/<carpeta en minusculas>/` |
| `PROCESADOS/` | `data/processed/` |
| `MODELOS/*.joblib`, `*.keras` | `models/registry/` |
| `MODELOS/*.json`, `*.csv` | `models/metadata/` |

El montaje de Drive (`from google.colab import drive` y `drive.mount(...)`) se elimino de los
catorce cuadernos. **No queda ninguna dependencia de Colab en el codigo**; el unico `!pip install`
que sobrevive funciona igual en Jupyter local.

La raiz se resuelve buscando hacia arriba, no con rutas relativas fijas: el cuaderno corre igual
si se lanza desde su propia carpeta o desde la raiz del proyecto.

**Requisito para ejecutarlos:** `data/raw/` y `data/processed/` deben estar poblados. No se
versionan por tamano; vease `docs/FUENTES.md` para la redescarga.

### Sobre las salidas guardadas

Las celdas conservan sus salidas de la ejecucion original, que son la evidencia de los Sprints.
Algunas de esas salidas imprimen la ruta de Drive antigua. El codigo esta limpio; el texto
impreso es historico.
