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

### Precisión: cuatro cuantos lógicos, tres unidades de despliegue

El sistema se organiza en **cuatro cuantos lógicos** con fronteras verificadas por prueba
automatizada, desplegados como **monolito modular** (Richards y Ford, 2020, cap. 8, p. 115).
Contrastados uno por uno contra los tres criterios de Ford et al. (2021, cap. 2, pp. 29-30):

| Cuanto | Desplegable de forma independiente | Alta cohesión funcional | Acoplamiento estático | Veredicto |
|--------|-----------------------------------|-------------------------|-----------------------|-----------|
| **Q1 · Ingesta** | Sí: proceso por lotes, se ejecuta solo | Sí: transformación del dato crudo | Bajo, limitado a librerías de procesamiento | **Cuanto físico** |
| **Q2 · Modelamiento** | No: vive en el proceso del servicio | Sí | **Extremo con Q3**: comparten proceso y binarios | Parte de un cuanto con Q3 |
| **Q3 · Servicio** | No: importa Q2 directamente | Sí | **Extremo con Q2** | Parte de un cuanto con Q2 |
| **Q4 · Cliente** | Sí: se compila a estáticos | Sí | Nulo con el backend, solo HTTP/JSON | **Cuanto físico** |

**Q2 y Q3 constituyen un único cuanto físico.** Comparten espacio de proceso —el mismo servidor
de aplicación—, comparten binarios y el grafo de dependencias declara `q3_servicio → q2_modelamiento`.
Bajo la definición que este documento cita, eso anula la independencia de despliegue.

**La decisión es deliberada, no un descuido.** La conascencia síncrona entre ambos es un requisito
de latencia: el simulador exige respuesta inmediata y una comunicación asíncrona degradaría la
interactividad. Separarlos en microservicios introduciría coordinación de despliegue,
observabilidad distribuida y latencia de red para resolver un problema que este sistema no tiene:
baja concurrencia, usuarios acotados y un fenómeno de periodicidad bianual. Es la aplicación del
criterio de la **arquitectura menos mala** (Richards y Ford, 2020, cap. 4, p. 63): no la mejor en
abstracto, sino la que mejor equilibra los compromisos de este dominio.

La partición lógica en cuatro se conserva porque es real: organiza el código, delimita
responsabilidades y está verificada por máquina. Lo que se precisa es cómo se declara el
despliegue.

---

### Taxonomía de las características de arquitectura

Las fuerzas de la tabla anterior se clasifican, según Richards y Ford (2020, cap. 4), en tres
categorías. La clasificación no es decorativa: determina dónde se verifica cada característica.

| Fuerza del dominio | Característica | Categoría |
|--------------------|----------------|-----------|
| Consecuencia monetaria del índice | Auditabilidad e integridad | Transversal |
| Escrutinio político y técnico | Explicabilidad y transparencia | Transversal |
| Datos de desempeño docente | Seguridad | Transversal |
| Simulación intensiva | Rendimiento | Operacional |
| Periodicidad bianual | Mantenibilidad y simplicidad | Estructural |

Los autores distinguen además entre características **explícitas**, derivadas de los requisitos
declarados, e **implícitas**, que el arquitecto infiere del contexto sin que nadie las pida
(Richards y Ford, 2020, cap. 5, p. 73). En este sistema son explícitas la estimación del índice,
el desglose por factor y la explicabilidad. Son implícitas la integridad de la serie histórica y
la seguridad del acceso: nadie escribió "el sistema no debe perder datos de establecimientos",
y sin embargo perderlos invalidaría el proyecto entero.

---

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

## 3.bis Estilos internos, conascencia y contratos

El estilo hexagonal describe la relación entre dominio e infraestructura, pero no dice nada sobre
cómo se organiza cada cuanto por dentro. Richards y Ford (2020) catalogan tres estilos que este
sistema aplica sin haberlos declarado hasta ahora.

| Cuanto | Estilo interno | Cita | Cómo se reconoce |
|--------|----------------|------|------------------|
| Q1 · Ingesta | Tubería y filtros | cap. 11, p. 143 | La secuencia leer → normalizar → filtrar → particionar → persistir es unidireccional y cada etapa transforma sin conocer a las demás |
| Q3 · Servicio | Capas con capas cerradas | cap. 10, p. 135 | `router → servicio → repositorio`. Ningún router alcanza la persistencia: la fachada se interpone siempre, y esa clausura protege las reglas de negocio de cambios en el esquema |
| Q2 · Modelamiento | Microkernel | cap. 12, p. 150 | El registro resuelve estrategias por clave y el núcleo no las conoce: añadir una arquitectura algorítmica es registrar una clase. El registro es **explícito**, no por descubrimiento —`fabrica.registrar(...)` al final del módulo—, de modo que la topología es de microkernel pero la carga no es dinámica |

La vista completa del sistema por capas —las cuatro capas, la regla de dependencia, el recorrido
de una petición y los tres puntos donde la clausura no se cumple— está en
`docs/capas/VISTA_EN_CAPAS.md`. Este documento describe la arquitectura por cuantos; aquel la
describe por capas, y su sección 6 explica por qué ninguna de las dos vistas sobra.

La correspondencia del microkernel es de topología, no de identidad: a nivel de patrón, el mismo
mecanismo se documenta en `docs/PATRONES_DE_DISENO.md` como Registry más Factory Method. Los dos
niveles describen la misma estructura con vocabularios distintos.

### Conascencia entre cuantos

La conascencia mide el grado de acoplamiento por el cual un cambio en un elemento obliga a
cambiar otro para conservar la corrección (Richards y Ford, 2020, cap. 3, p. 48).

| Frontera | Tipo de conascencia | Consecuencia |
|----------|--------------------|--------------|
| Q3 → Q2 | Estática, de nombre y de tipo | Es la forma deseable: el sistema de tipos la detecta antes de ejecutar |
| Q3 → Q4 | Dinámica, de valor | Un cambio en el contrato JSON solo se manifiesta en tiempo de ejecución |

La **regla de localidad** (cap. 3, p. 52) explica por qué la primera es aceptable: Q3 y Q2 se
despliegan en el mismo proceso, y formas fuertes de conascencia son tolerables cuando los
elementos están próximos. Si fueran servicios separados, la misma conascencia obligaría a
coordinar despliegues.

### Clasificación de los contratos

| Contrato | Clasificación | Fundamento |
|----------|--------------|------------|
| `EstrategiaPredictiva` | **Estricto** (Ford et al., 2021, cap. 13, p. 365) | Cualquier cambio de firma invalida al consumidor de inmediato. Es lo correcto en el núcleo: impide que el simulador produzca resultados inconsistentes |
| Interfaz JSON hacia Q4 | Debería ser **laxo** (p. 367) | El cliente debe tolerar campos añadidos sin romperse, para que la interfaz evolucione sin despliegues acoplados |

### Acoplamiento de estampilla: caso verificado

Ford et al. (2021, cap. 13, p. 376) advierten sobre el *stamp coupling*: enviar una estructura
completa cuando el consumidor solo necesita una parte. **En este sistema no es un riesgo
hipotético, está ocurriendo y es medible.**

`GET /api/v1/establecimientos/{rbd}` devuelve la observación ancha completa —66 variables— y el
tablero del sostenedor utiliza exactamente **dos**: `nom_rbd` y `matricula_total`. El resto viaja
por la red, se deserializa y se descarta.

Queda declarado como deuda: la solución es un objeto de transferencia acotado a lo que el
consumidor consume, o un parámetro de proyección de campos. No se corrige aquí porque alteraría
un contrato hoy verificado por la prueba de paridad.

---

### Deudas que este análisis dejó declaradas

| Deuda | Evidencia | Solución de fondo |
|-------|-----------|-------------------|
| Acoplamiento de estampilla | 66 variables enviadas, 2 utilizadas | Objeto de transferencia acotado o proyección por parámetro |
| El contrato hacia Q4 no es laxo | Tipos escritos a mano en vez de generados desde el esquema publicado | Adoptar `npm run tipos` y declarar tolerancia a campos añadidos |
| CTRL-03 sin evidencia | No existe línea base de distribuciones en `models/metadata/` | Generarla en la próxima publicación de artefactos |
| CTRL-04 y CTRL-05 apuntan a tablas vacías | `app.auditoria`, `ml.inferencia` e `ml.inferencia_atribucion` creadas y sin escrituras | Depende de migrar el directorio de usuarios a `app.usuario` |

---

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

`scripts/verificar_arquitectura.py` corresponde a una **función de aptitud atómica** (Richards y
Ford, 2020, cap. 6, p. 83): una comprobación objetiva y automatizable que gobierna una
característica arquitectónica —aquí, la mantenibilidad— y que se ejecuta en cada integración. Su
valor es que convierte la frontera entre cuantos en algo que una máquina puede refutar, no en una
convención que depende de la disciplina de quien escribe el código.


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

---

## 9. Impulsores de modularidad

Ford et al. (2021, cap. 3) catalogan las razones legítimas para partir un sistema. De ese
catálogo, dos aplican a este proyecto y el resto no:

| Impulsor | Cita | Cómo opera aquí |
|----------|------|-----------------|
| Mantenibilidad | pp. 50 | Permite modificar la lógica de cálculo ante un cambio normativo sin efectos colaterales en la ingesta ni en la interfaz |
| Testabilidad | pp. 54 | Cada cuanto se prueba por separado: la suite corre sin base de datos ni artefactos gracias a los marcadores de exclusión |

**Escalabilidad y tolerancia a fallos no son impulsores de esta partición.** El sistema no tiene
escalabilidad elástica ni la necesita: no existen picos de carga, sino consultas de equipos
directivos sobre un fenómeno que se calcula cada dos años. Y la explicabilidad, que en algún
análisis podría confundirse con tolerancia a fallos, es una característica transversal de
transparencia: no protege al sistema de fallar, sino que hace legible su resultado.

## 10. El módulo compartido como componente de dominio común

`quanta/compartido/` corresponde a lo que Ford et al. (2021, cap. 5, p. 94) denominan
**componente de dominio común**: código que los cuatro cuantos necesitan por igual y que no
pertenece a ninguno.

La advertencia de la fuente es pertinente: si un componente así acumula lógica de negocio, se
vuelve rígido sin volverse abstracto y se desplaza hacia la zona de dolor en la métrica de
distancia a la secuencia principal (p. 69). Hoy contiene únicamente el mecanismo componible de
especificaciones y la resolución de rutas del proyecto. **Ese es su límite y conviene vigilarlo:**
la señal de alarma es que alguna regla del dominio SNED aparezca ahí en lugar de en el cuanto que
la posee.

### Una simetría entre el código y los datos

El esquema `core` cumple en la base de datos exactamente el mismo papel que `quanta/compartido/`
cumple en el código. La verificación del modelo físico lo confirma: las 27 claves foráneas que
cruzan esquemas apuntan **todas** hacia `core` —18 desde `hechos`, 5 desde `ml` y 4 desde `app`—
y no existe ninguna referencia lateral entre `hechos`, `ml` y `app`. Es una topología de estrella
con el catálogo al centro.

La consecuencia es que la separación de dominios de datos **es efectiva**, no ilusoria: ingesta y
servicio no comparten tablas. El único punto donde se tocan es la vista materializada
`ml.mv_matriz_entrenamiento`, que lee de `hechos` y de `core`; pero es lectura, no restricción
estructural, y tender ese puente es precisamente su función.

Ambos componentes comparten también el mismo riesgo: son referenciados por todos y no dependen de
nadie, de modo que cualquier lógica de negocio que se filtre en ellos se propaga a todo el
sistema sin que ninguna frontera la detenga.

## 11. El parquet como cuanto de producto de datos

Los archivos columnares no son una copia de la base ni un respaldo. Constituyen un **cuanto de
producto de datos** (Ford et al., 2021, cap. 14, p. 390): un artefacto analítico con su propio
ciclo de vida, distinto del de la base operacional, servido a un consumidor identificado —el
entrenamiento— y optimizado para su patrón de acceso.

Eso explica por qué el adaptador de parquet se conserva incluso después de migrar a PostgreSQL:
no es redundancia, son dos productos de datos con propósitos diferentes.

## 12. Declaración de no aplicabilidad

Declarar qué no aplica es parte del rigor: evita que un lector suponga omisiones donde hay
decisiones.

| Elemento de la bibliografía | Por qué no aplica |
|------------------------------|-------------------|
| Sagas transaccionales y compensatorias (Ford et al., 2021, cap. 12) | Una sola base de datos, sin escrituras concurrentes distribuidas. No hay consistencia eventual que gestionar |
| Propiedad distribuida de datos | Todos los esquemas viven en la misma instancia, bajo integridad referencial |
| Coreografía y orquestación de flujos distribuidos | El flujo es lineal y consultivo: una petición, una respuesta |
| Malla de datos descentralizada | El sistema es un único producto de datos, no un nodo de una malla |
| Vehículos secundarios para funcionalidad transversal | Sobrecarga operacional injustificada para un sistema por lotes de ciclo bianual |

## 13. Reconocimiento del sesgo metodológico

Aplicar a este sistema un marco concebido para arquitecturas distribuidas de gran escala conlleva
el riesgo del **análisis fuera de contexto** (Ford et al., 2021, cap. 15, p. 405). Las métricas de
acoplamiento, los criterios de cuanto y las clasificaciones de contrato fueron formulados para
sistemas con decenas de servicios y equipos independientes; este es un simulador con dos unidades
de despliegue y un solo desarrollador.

El análisis se conserva por dos razones. La primera es que los criterios de cuanto revelaron una
imprecisión real en la documentación —la independencia de despliegue que se afirmaba de Q2 y Q3—
que de otro modo habría llegado sin corregir a la defensa. La segunda es que el vocabulario
permite declarar con precisión qué se hizo y qué no, que es el propósito de un documento de
arquitectura.

Lo que **no** debe inferirse es que este sistema necesite crecer hacia esa escala para ser válido.

---

## Referencias

- Cockburn, A. (2005). *Hexagonal Architecture (Ports and Adapters)*.
- Ford, N., Richards, M., Sadalage, P. y Dehghani, Z. (2021). *Software Architecture: The Hard
  Parts*. O'Reilly Media.
- Richards, M. y Ford, N. (2020). *Fundamentals of Software Architecture: An Engineering
  Approach*. O'Reilly Media.

**Nota de atribución.** Ninguna de las dos obras de Ford y Richards documenta la arquitectura
hexagonal: ese estilo se atribuye a Cockburn (2005). El respaldo que aportan opera sobre la
partición en cuantos, los estilos internos de cada uno y la clasificación de contratos, no sobre
el estilo hexagonal en sí.
