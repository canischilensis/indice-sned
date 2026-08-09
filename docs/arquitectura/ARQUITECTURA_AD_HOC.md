# Arquitectura de software implementada

Identificador del documento: **AR-SNED-01**

Documento de arquitectura *aplicada*: muestra dónde se ve cada decisión estructural en los
artefactos UML y en el código. El documento hermano `docs/ARCHITECTURE.md` justifica las
decisiones; este muestra que están efectivamente implementadas.

---

## 1. Estilo adoptado

**Arquitectura hexagonal (puertos y adaptadores) particionada en cuantos de arquitectura.**

No es una elección de catálogo. Se deriva de cuatro fuerzas del dominio:

| Fuerza del dominio | Consecuencia estructural |
|--------------------|-------------------------|
| El índice tiene consecuencia monetaria directa | Se acepta complejidad distribuida a cambio de auditabilidad |
| Los criterios de subvención cambian por ciclo político | Las reglas volátiles quedan tras puertos, no incrustadas |
| El directivo necesita saber *qué mover*, no solo *cuánto obtendrá* | La explicabilidad es núcleo, no anexo |
| El fenómeno es bianual | Se excluye la orquestación de MLOps por deuda técnica |

Un **cuanto de arquitectura** es una unidad desplegable de forma independiente, con alta
cohesión funcional y acoplamiento controlado (Ford, Richards, Sadalage y Dehghani, 2021,
*Software Architecture: The Hard Parts*). El sistema tiene cuatro.

## 2. Dónde se ve la arquitectura en los artefactos UML

Esta es la parte que suele quedar implícita. Cada elemento arquitectónico tiene un lugar
concreto en un diagrama concreto.

| Elemento arquitectónico | Artefacto UML donde se observa | Cómo se reconoce |
|------------------------|-------------------------------|------------------|
| Puerto | `01_hexagonal.png` | Clase abstracta con operaciones sin cuerpo, en el anillo interior |
| Adaptador | `01_hexagonal.png` | Clase concreta en el anillo exterior, con flecha de realización hacia el puerto |
| Frontera de cuanto | `01_hexagonal.png` | Agrupación con nombre `qN_*`; ninguna flecha la cruza fuera del grafo permitido |
| Inversión de dependencia | `03_secuencia_prediccion.png` | El router llama a la fachada, la fachada al puerto; **ningún mensaje va del dominio hacia la infraestructura** |
| Carga diferida | `05_secuencia_shap.png` | El mensaje `materializar()` aparece dentro del primer `explicar()`, no en la construcción |
| Estrategia intercambiable | `02_patrones.png` | Dos clases concretas realizando `EstrategiaPredictiva`, sin que el servicio conozca cuál |
| Decoración | `02_patrones.png` | Clases que realizan el puerto y a la vez lo contienen |
| Repositorio con dos adaptadores | `02_patrones.png` | `RepositorioParquet` y `RepositorioPostgres` sobre el mismo contrato |

Los cinco diagramas se derivaron del código real, no al revés. La regla que se siguió al
generarlos fue explícita: **no se refactorizó código para que los diagramas quedaran más
limpios**. Donde el diagrama es incómodo, el código lo es.

## 3. Los cuatro cuantos

### Q1 · Ingesta

Único cuanto autorizado a tocar archivos crudos. Entrega parquet normalizado. No conoce el
motor predictivo ni el marco web.

Patrones: Template Method (el orden de los pasos de ingesta es invariante, la lectura varía),
Specification (las reglas de admisión se componen con `y`, `o`, `no`), Adapter (una fuente por
formato y codificación), Pipes and Filters (leer → normalizar → filtrar → particionar →
persistir).

### Q2 · Modelamiento

Único cuanto que conoce scikit-learn, TensorFlow y shap. Expone `EstrategiaPredictiva`.
Contiene el registro de artefactos (CTRL-05), el protocolo de validación anti-fuga (CTRL-02) y
la verificación de deriva (CTRL-03).

Patrones: Strategy, Decorator (auditoría y caché), Factory Method, Registry, Virtual Proxy
(carga diferida), Builder (construcción de escenarios).

### Q3 · Servicio

Encapsula el motor tras HTTP y aplica el control de acceso por jurisdicción (CTRL-04).
**Prohibido importar librerías de aprendizaje automático**; la prueba de arquitectura lo
verifica en cada ejecución de la suite.

Patrones: Repository, Facade (`ServicioDePrediccion`), Adapter, Specification (reglas de
alerta).

### Q4 · Cliente

Tres ventanas funcionales. Consume exclusivamente JSON tipado. Desconoce por completo qué
algoritmo hay detrás: ese desconocimiento es el criterio de éxito de la frontera Strategy.

Patrones de dominio: ninguno, por diseño. Un patrón de dominio en el cliente sería dominio
duplicado.

## 4. La frontera crítica

```python
# quanta/q2_modelamiento/contrato.py
class EstrategiaPredictiva(ABC):
    def predecir(self, observacion) -> Prediccion
    def explicar(self, observacion, factor) -> ExplicacionLocal
    def simular(self, observacion, variable, rango) -> CurvaSensibilidad
```

Verificación empírica de que el patrón sostiene: durante el desarrollo se compararon tres
arquitecturas de aprendizaje —árboles con potenciación por histograma, perceptrón multicapa y
bosque aleatorio— sobre la misma representación de entrada **sin alterar una línea de la capa
de servicio**.

La segunda frontera, verificada más tarde, es la de persistencia:

```python
# quanta/q3_servicio/repositorios/fabrica.py
ADAPTADORES = {"parquet": RepositorioParquet, "postgres": RepositorioPostgres}
PREDETERMINADO = "postgres"
```

Conmutar la fuente es fijar una variable de entorno. La equivalencia se verificó campo por
campo sobre 141 llamadas.

## 5. Controles de arquitectura

Un control es una restricción que el sistema se impone y verifica sobre sí mismo.

| ID | Riesgo mitigado | Dónde actúa | Evidencia que produce |
|----|-----------------|-------------|----------------------|
| CTRL-01 | Orfandad e integridad referencial | Ingesta | Parquet de cuarentena + reporte de calidad |
| CTRL-02 | Fuga de datos | Preprocesamiento y entrenamiento | Excepción `FugaDeDatos`; R² del predictor trivial ≈ 0 |
| CTRL-03 | Deriva postpandemia | Verificación bianual | Línea base de distribuciones + registro de contraste |
| CTRL-04 | Acceso no autorizado | Servicio y visualización | Respuesta 403 y pruebas de control de acceso |
| CTRL-05 | Pérdida de trazabilidad | Registro de modelos | Artefactos versionados; tablas `ml.inferencia` |

## 6. Compuerta de incorporación del incremento

Un incremento pasa a *Terminado* solo si supera, en orden, tres barreras:

1. **Código y estructura de datos** — análisis estático, tipado, esquema de base de datos,
   auditoría anti-fuga.
2. **Criterios de aceptación** — pruebas de integración. Un fallo de control de acceso reprueba
   la barrera completa, sin excepción.
3. **Umbral de precisión** — el modelo candidato se aprueba solo si supera al vigente **y** la
   superioridad se sostiene con intervalos de confianza y prueba t pareada.

Si falla cualquiera, el incremento se rechaza, retorna al backlog y se preserva la última
versión estable de los artefactos serializados.

## 7. Compromisos asumidos y declarados

| Compromiso | Se gana | Se paga | Decisión |
|-----------|---------|---------|----------|
| Motor desagregado frente a global | Trazabilidad variable → factor → índice | 0,054 de R² | Conservar ambos, con funciones distintas |
| Complejidad distribuida | Auditabilidad, despliegue independiente | Latencia de red, más piezas móviles | Aceptado |
| Sin MLOps | Cero deuda de orquestación | Reentrenamiento manual bianual | Aceptado: el fenómeno es bianual |
| Preprocesamiento uniforme en la comparación | Validez interna del contraste | Neutraliza el manejo nativo de nulos de un algoritmo | Aceptado; el desempeño reportado es cota inferior |
| Árboles sobre red neuronal | Shapley exacto, sin GPU, serialización simple | ≈ 0,007 de R², estadísticamente equivalente | Criterio arquitectónico, no métrico |

## 8. Frontera de información irreducible

Cinco de los seis factores están acotados por información que el organismo emisor no publica.
No es un defecto del modelo: es un diagnóstico verificable sobre las condiciones de
replicabilidad externa del cálculo estatal.

| Factor | Peso | R² | Restricción |
|--------|------|-----|-------------|
| Efectividad | 37 % | 0,832 | ninguna |
| Superación | 28 % | 0,200 | corrección por significancia estadística no publicada |
| Igualdad de oportunidades | 22 % | 0,128 | subtipo de sanción por discriminación no desagregado |
| Iniciativa | 6 % | 0,084 | ficha de autorreporte no pública |
| Integración | 5 % | 0,132 | ficha de autorreporte no pública |
| Mejoramiento | 2 % | 0,024 | varianza del objetivo próxima a cero |

**El 63 % de la ponderación está acotada.** El campo `es_acotado` viaja en cada respuesta de la
interfaz de programación y se renderiza en el tablero: la limitación es parte del producto, no
una nota al pie.
