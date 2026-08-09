# Diseño del software y modelo de clases

Identificador del documento: **DS-SNED-01**

Describe la estructura interna que realiza los casos de uso. El criterio de organización es la
**dimensión de cambio**: cada abstracción existe para aislar algo que se espera que varíe. Una
abstracción que no aísla ninguna variación es indirección gratuita y no debería existir.

Diagramas: `docs/diagramas/01_hexagonal.png` (puertos y adaptadores) y `02_patrones.png` (los
doce patrones sobre el código real).

---

## 1. Módulo compartido

### `Especificacion[T]`

Clase abstracta genérica con una operación: `es_satisfecha_por(candidato) -> bool`. Aporta tres
combinadores —`y`, `o`, `no`— implementados como conjunción, disyunción y negación privadas.

Existe porque el sistema tiene dos familias de reglas volátiles —admisión de datos y emisión de
alertas— que deben poder combinarse sin reescribirse. `EspecificacionPredicado` permite envolver
una función suelta cuando la regla no merece una clase.

**Por qué no un simple `if`:** las reglas de admisión provienen de normativa y se citan una por
una en el reporte de calidad. Necesitan nombre, identidad y composición.

## 2. Cuanto 1 · Ingesta

| Clase | Responsabilidad | Patrón |
|-------|-----------------|--------|
| `IngestorDeFuente` | Fija el orden invariante de la ingesta y delega la lectura | Template Method |
| `IngestorExcel`, `IngestorCsv`, `IngestorCsvUtf8` | Resuelven formato y codificación | Adapter |
| `Fuente` | Describe una fuente pública: ruta, formato, llave, ventana | — |
| `RegistroCandidato` | Envuelve una fila para que las reglas la interroguen sin conocer el marco de datos | — |
| `TieneRbdValido`, `TieneAnioValido`, `LlaveEsUnica`, `DentroDeVentanaTemporal`, `FichaInstitucionalRespondida` | Reglas de admisión | Specification |
| `ReporteCalidad` | Cobertura de llave, cumplimiento de umbral y resumen legible | — |

El método plantilla `ejecutar()` fija seis pasos: leer, normalizar el identificador, evaluar
reglas, particionar, persistir ambas particiones, emitir reporte. Las subclases solo pueden
alterar la lectura.

**Regla de dominio incrustada en el diseño:** los registros rechazados van a cuarentena, no al
descarte. La partición devuelve dos conjuntos y ambos se persisten.

## 3. Cuanto 2 · Modelamiento

### El puerto

```python
class EstrategiaPredictiva(ABC):
    @property
    def variables_requeridas(self) -> list[str]
    def predecir(self, observacion) -> Prediccion
    def explicar(self, observacion, factor=None) -> ExplicacionLocal
    def simular(self, observacion, variable, rango=None, n_puntos=25) -> CurvaSensibilidad
    def describir(self) -> dict
```

### Objetos de valor del contrato

| Clase | Contenido | Invariante que protege |
|-------|-----------|------------------------|
| `Prediccion` | Índice estimado y desglose por factor | El índice se reconstruye desde los factores con las ponderaciones vigentes |
| `ExplicacionLocal` | Valor base y contribuciones por variable | `verificar_aditividad(1e-3)`: base + contribuciones = predicción |
| `ContribucionVariable` | Variable, valor, contribución, dirección | La dirección se deriva del signo, no se pasa por parámetro |
| `CurvaSensibilidad` | Malla de valores y respuesta del índice | `es_monotona_creciente()` permite detectar curvas implausibles |

### Las dos estrategias

| Clase | Cómo estima | Explicabilidad | R² |
|-------|-------------|----------------|-----|
| `EstrategiaDesagregada` | Un modelo por factor; el índice se reconstruye ponderando | Sí, por factor | 0,583 |
| `EstrategiaGlobal` | Un modelo sobre el índice completo | No por factor | 0,637 |

Conviven porque responden preguntas distintas: la global estima mejor, la desagregada dice
**qué mover**. El simulador usa la desagregada, y por eso su R² inferior es un costo aceptado y
declarado, no un descuido.

**Imputación con bandera de ausencia.** La estrategia desagregada no rellena silenciosamente:
imputa por mediana **y** añade una variable indicadora `<variable>_ausente`. El modelo sabe
cuándo está mirando un valor real y cuándo un relleno. Las etiquetas legibles traducen esas
banderas como "Sin medición de …", nunca como un valor.

### Infraestructura del cuanto

| Clase | Responsabilidad | Patrón |
|-------|-----------------|--------|
| `FabricaDeEstrategias` | Resuelve nombre → instancia; las estrategias se auto-registran | Factory Method + Registry |
| `RegistroDeModelos` | Inventario de artefactos, metadatos y medianas de imputación | Registry |
| `ArtefactoDiferido` | Envuelve un artefacto y lo carga en el primer uso | Virtual Proxy |
| `DecoradorDeEstrategia` | Base para envolver una estrategia sin modificarla | Decorator |
| `EstrategiaAuditada` | Registra cada inferencia servida | Decorator |
| `EstrategiaConCache` | Memoriza predicciones por observación | Decorator |
| `ConstructorDeEscenario` | Construye escenarios válidos paso a paso | Builder |
| `Escenario` | Conjunto inmutable de cambios sobre una observación | — |
| `Factor` | Código, nombre, peso, restricción; deriva `es_acotado` | — |

**Detalle de implementación relevante:** `ArtefactoDiferido` expone `predict`, de modo que se
comporta como el modelo que envuelve. El explicador de Shapley, sin embargo, inspecciona el
tipo del objeto y rechaza el envoltorio; por eso la construcción del explicador invoca
`materializar()` de forma explícita. Es la fuga clásica del proxy virtual, y está resuelta en un
solo punto.

## 4. Cuanto 3 · Servicio

| Clase | Responsabilidad | Patrón |
|-------|-----------------|--------|
| `RepositorioEstablecimientos` | Puerto de persistencia: `obtener`, `listar`, `ranking`, `existe`, `describir` | Repository |
| `RepositorioParquet` | Adaptador sobre archivos columnares | Adapter |
| `RepositorioPostgres` | Adaptador sobre la base relacional | Adapter |
| `ServicioDePrediccion` | Fachada: compone repositorio, estrategia y reglas de alerta | Facade |
| `ContextoDeAlerta` | Vista de solo lectura de la estimación y las variables | — |
| `ReglaDeAlerta` | Especificación que además construye la alerta que emite | Specification |
| `Usuario`, `Rol` | Identidad y jurisdicción | — |
| `Configuracion` | Configuración externa validada | — |

### La fachada

`ServicioDePrediccion` es el único punto donde se encuentran el repositorio y la estrategia. Los
routers no conocen ninguno de los dos. Sus operaciones: `variables_de`, `predecir`, `explicar`,
`simular`, `evaluar_alertas`, `diagnostico_de_cobertura`, `describir`.

`diagnostico_de_cobertura` descuenta las banderas `_ausente` antes de comparar, porque son
derivadas del propio motor y no variables que la fuente pueda proveer. Sin ese descuento, la
cobertura reportada sería falsa por construcción.

### Las cuatro reglas de alerta

| Regla | Se dispara cuando | Severidad |
|-------|-------------------|-----------|
| `TrampaDeSuperacion` | Efectividad alta con superación baja: el establecimiento ya está arriba y le queda poco margen de avance | Alta |
| `RiesgoNormativo` | Los eventos de fiscalización acumulados superan el umbral | Alta o media según cantidad |
| `CaidaIdps` | El promedio de indicadores de desarrollo personal cae bajo el umbral | Media |
| `FactorAcotadoDominante` | La mayor parte de la estimación descansa en factores acotados por información no publicada | Informativa |

La cuarta no es una alerta de gestión sino de epistemología: advierte al usuario de que el
sistema sabe menos de lo que su número sugiere.

## 5. Cuanto 4 · Cliente

| Componente | Función |
|-----------|---------|
| `App` | Sesión, selector de establecimiento y navegación entre las tres ventanas |
| `Login` | Autenticación |
| `Dashboard` | Estimación, desglose por factor y alertas |
| `Simulador` | Curva de sensibilidad sobre una variable |
| `ReporteXAI` | Contribuciones de Shapley por factor |
| `api.ts` | Único punto de contacto con el servicio; la sesión vive en memoria |
| `tipos.ts` | Tipos del contrato, regenerables desde el esquema OpenAPI |

**Sin patrones de dominio, por diseño.** El cliente no calcula el índice, no pondera, no decide
severidad. Si lo hiciera, habría dos implementaciones de la misma regla y una de ellas se
desactualizaría.

El token se guarda en memoria del módulo, no en almacenamiento del navegador: cerrar la pestaña
cierra la sesión.

## 6. Trazabilidad de patrones

Doce patrones aplicados y doce evaluados y descartados, con la fuerza que justifica cada uno y
su fuente citada, en `docs/PATRONES_DE_DISENO.md`.

| Cuanto | Patrones aplicados |
|--------|-------------------|
| Q1 · Ingesta | Template Method, Specification, Adapter, Pipes and Filters |
| Q2 · Modelamiento | Strategy, Decorator, Factory Method, Registry, Virtual Proxy, Builder |
| Q3 · Servicio | Repository, Facade, Adapter, Specification |
| Q4 · Cliente | ninguno de dominio, por diseño |

Los creacionales y estructurales se concentran donde vive la complejidad algorítmica y los
artefactos costosos; los de comportamiento donde viven las reglas que cambian por normativa.

## 7. Deuda de diseño conocida

| # | Deuda | Consecuencia | Solución de fondo |
|---|-------|--------------|-------------------|
| 1 | El directorio de usuarios vive en memoria | No hay administración de usuarios | Migrar a `app.usuario`, ya creada |
| 2 | Ocho variables derivadas se calculan en el entrenamiento y no se persisten | Cobertura de 35/43 = 81,4 %; el servicio las imputa | Materializarlas en `hechos.indicador_anual` durante la ingesta |
| 3 | Los artefactos están acoplados a la versión de la librería con que se entrenaron | Fallan con una versión mayor distinta | Registrar la versión en los metadatos y verificarla al cargar |
| 4 | La simulación no reutiliza cómputo entre puntos de la malla | 4,6 s por llamada | Vectorizar la malla en una sola inferencia por modelo |
