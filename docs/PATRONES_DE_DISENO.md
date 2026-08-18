# Patrones de diseño en la arquitectura del ecosistema SNED

**Documento de decisión arquitectónica.** Analiza los cuatro cuantos del sistema, identifica
las fuerzas reales presentes en el código y justifica qué patrones se aplican, cuáles se
descartan y por qué.

> **Criterio rector.** Un patrón se aplica cuando existe una *fuerza* que lo justifica —una
> tensión concreta en el diseño— y no porque figure en el catálogo. Gamma et al. (1994) son
> explícitos: los patrones describen soluciones a problemas *recurrentes en un contexto*.
> Aplicar un patrón sin su contexto es sobreingeniería, y la sobreingeniería es deuda técnica
> con mejor prensa.

---

## 0. Por qué este sistema necesita patrones más que un sistema convencional

Sculley et al. (2015) documentan que en los sistemas de aprendizaje automático **"un sistema
maduro puede terminar siendo (como máximo) 5 % código de machine learning y (como mínimo)
95 % código de pegamento"**, y advierten sobre **"una marcada ausencia de abstracciones fuertes
para soportar sistemas de ML"**, comparándolo desfavorablemente con las bases de datos:
*"nada en la literatura de machine learning se acerca al éxito de la base de datos relacional
como abstracción básica"*.

Ese vacío es exactamente el que los patrones de diseño llenan aquí. Los tres antipatrones que
el paper describe tienen correspondencia directa en este proyecto:

| Antipatrón (Sculley et al., 2015) | Riesgo concreto en el ecosistema SNED | Patrón que lo neutraliza |
|---|---|---|
| *Glue code* | El simulador queda soldado a la API de scikit-learn | **Strategy** (ya aplicado) |
| *Pipeline jungles* — "una jungla de raspados, uniones y muestreos" | 12 fuentes MINEDUC declaradas con lógica duplicada | **Template Method** + **Pipes and Filters** |
| *Configuration debt* — "cada línea de configuración es una oportunidad de error" | Ponderaciones y reglas incrustadas en código | **Registry** + **Specification** |
| CACE — *"Changing Anything Changes Everything"* | Un cambio normativo corrompe silenciosamente las proyecciones | **Specification** + **Registry** |

---

## 1. Mapa de patrones aplicados

| # | Patrón | Categoría | Fuente | Cuanto | Fuerza que lo justifica |
|---|--------|-----------|--------|--------|-------------------------|
| P1 | **Strategy** | Comportamiento (GoF) | Gamma et al. (1994); Freeman et al. (2004) | Q2 | *Ya aplicado.* No se sabe a priori qué arquitectura gana |
| P2 | **Repository** | Arquitectura empresarial | Fowler (2002) | Q3 | La capa de servicio lee parquet directamente; en producción debe leer PostgreSQL |
| P3 | **Template Method** | Comportamiento (GoF) | Gamma et al. (1994) | Q1 | 12 fuentes con esqueleto idéntico y solo el *parsing* distinto |
| P4 | **Specification** | Diseño dirigido por dominio | Evans (2003); Evans y Fowler (2002) | Q1, Q3 | Reglas de cuarentena y de alerta como cadenas de `if` que crecen |
| P5 | **Decorator** | Estructura (GoF) | Gamma et al. (1994) | Q2 | CTRL-05 exige auditar *toda* inferencia sin contaminar las estrategias |
| P6 | **Factory Method** | Creación (GoF) | Gamma et al. (1994) | Q2 | La resolución de estrategias es una función suelta con un `dict` global |
| P7 | **Facade** | Estructura (GoF) | Gamma et al. (1994) | Q3 | `motor.py` ya actúa como fachada, sin ser una |
| P8 | **Builder** | Creación (GoF) | Gamma et al. (1994) | Q2 | Los escenarios contrafactuales se construyen con `dict(base); base[v]=x` disperso |
| P9 | **Virtual Proxy / Lazy Load** | Estructura (GoF); Fowler (2002) | Gamma et al. (1994) | Q2 | Artefactos de 60 MB cargados de forma diferida, hoy de manera implícita |
| P10 | **Registry** | Arquitectura empresarial | Fowler (2002) | Q2 | Catálogo de factores y de modelos accesibles por clave, sin globales dispersas |
| P11 | **Adapter** | Estructura (GoF) | Gamma et al. (1994) | Q1, Q3 | Puertos hexagonales con implementaciones intercambiables |
| P12 | **Pipes and Filters** | Arquitectura | Buschmann et al. (1996); Richards y Ford (2020) | Q1 | El ETL es literalmente una cadena de filtros sobre un flujo |

---

> **Ordenados por capa:** esta tabla mapea cada patrón a su **cuanto**. El mismo conjunto ordenado
> por **capa** —presentación, aplicación, dominio, persistencia— está en
> `docs/capas/PATRONES_POR_CAPA.md`. No hay patrones nuevos allí: es el otro eje de lectura.

## 1.bis Principios de diseño que gobiernan los cuatro cuantos

Los patrones no son la unidad de decisión más pequeña: debajo de cada uno hay un principio que
lo justifica. Freeman et al. (2020) los presentan como criterios de separación de
responsabilidades, no como reglas. La tabla los mapea contra los cuatro cuantos del sistema, de
modo que la frontera entre cuantos deje de ser una convención y pase a tener fundamento citable.

| Principio | Cita | Dónde se observa en esta arquitectura |
|-----------|------|----------------------------------------|
| Identificar los aspectos que varían y separarlos de lo que permanece igual | Cap. 1, p. 9 | Es el fundamento de la arquitectura hexagonal completa. Cada puerto aísla exactamente una dimensión de cambio: el algoritmo, el medio de persistencia, el formato de la fuente y la regla de negocio |
| Programar a una interfaz, no a una implementación | Cap. 1, p. 11 | Q2 expone el motor únicamente a través de `EstrategiaPredictiva`. El resto del sistema es agnóstico respecto de si detrás hay un bosque aleatorio o una red neuronal |
| Favorecer la composición sobre la herencia | Cap. 1, p. 23 | El comportamiento de auditoría y de caché se obtiene componiendo decoradores en tiempo de ejecución, no extendiendo la jerarquía de estrategias |
| Principio Abierto-Cerrado: abierto a la extensión, cerrado a la modificación | Cap. 3, p. 86 | Una regla de alerta nueva en Q3 se registra sin tocar el flujo de evaluación, porque cada regla es una especificación componible |
| Inversión de dependencias: depender de abstracciones, no de clases concretas | Cap. 4, p. 139 | En Q3 no es solo un principio: es una **restricción verificada**. El cuanto tiene prohibido importar librerías de aprendizaje automático y una prueba automatizada lo comprueba en cada ejecución |
| Principio de Hollywood: no nos llames, nosotros te llamaremos | Cap. 8, p. 296 | El esqueleto de ingesta de Q1 decide cuándo invocar la lectura concreta de cada fuente. La subclase no controla el orden: solo responde cuando se la llama |
| Principio del menor conocimiento (Ley de Demeter) | Cap. 7, p. 265 | Q4 consume exclusivamente JSON tipado. Tiene prohibido conocer las librerías internas de Q2 o la complejidad algorítmica del motor |
| Principio de responsabilidad única: una clase, una sola razón para cambiar | Cap. 9, p. 339 | Fundamenta la existencia misma de los cuantos: la calidad del dato (Q1) y la inferencia predictiva (Q2) cambian por razones distintas y en momentos distintos |

Dos de estas correspondencias merecen subrayarse porque no son declarativas sino comprobables:
la inversión de dependencias en Q3 y el menor conocimiento en Q4 están respaldadas por
`scripts/verificar_arquitectura.py`, que recorre las importaciones reales y falla si alguna sale
del grafo permitido. Un principio que una máquina puede refutar deja de ser una aspiración.

---

## 2. Patrones aplicados: justificación detallada

### P1 · Strategy — *ya presente, se documenta por completitud*

**Fuerza.** El teorema de la ausencia de almuerzo gratuito impide saber a priori qué
arquitectura algorítmica será superior. El sistema debía comparar tres familias con supuestos
inductivos distintos y sobrevivir a migraciones futuras.

**Fuente.** Gamma et al. (1994): *"define una familia de algoritmos, encapsula cada uno y los
hace intercambiables; Strategy permite que el algoritmo varíe independientemente de los
clientes que lo usan"*. Freeman et al. (2020) lo asocian al principio de favorecer la
composición sobre la herencia, citado explícitamente en el Capítulo 3 de la tesis.

**Definicion canonica.** Freeman et al. (2020, cap. 1, p. 24) definen Strategy como el patron
que *"define una familia de algoritmos, encapsula cada uno y los hace intercambiables, dejando
que el algoritmo varie independientemente de los clientes que lo usan"*. La obra lo presenta
como la materializacion directa del principio de programar a una interfaz.

**Dónde.** `quanta/q2_modelamiento/contrato.py` → `EstrategiaPredictiva`.

**Evidencia empírica de que sostiene.** Se compararon HistGradientBoosting, Perceptrón
multicapa y Random Forest sobre idéntica representación de entrada **sin alterar una sola línea
de la capa de servicio**. Esa es la verificación del patrón, no su enunciado.

---

### P2 · Repository — *acceso a establecimientos*

**Fuerza observada.** `quanta/q3_servicio/servicios/establecimientos.py:32` ejecuta
`pd.read_parquet(ruta)` dentro de la capa de servicio. El diseño declara PostgreSQL como
entregable formal con tres vistas de consumo, de modo que hoy existen **dos orígenes posibles
para el mismo dato** y el servicio conoce el detalle de uno de ellos. Cambiar de parquet a
PostgreSQL obligaría a tocar la capa de servicio: acoplamiento a infraestructura.

**Fuente.** Fowler (2002) define Repository como aquello que *"media entre el dominio y las
capas de mapeo de datos usando una interfaz similar a una colección para acceder a los objetos
de dominio"*. Las fuerzas que resuelve —abstracción sobre el acceso a datos, concentración de
la lógica de consulta y dependencia unidireccional del dominio hacia el mapeo— son literalmente
las que presenta este módulo.

**Aplicación.** Se declara el puerto `RepositorioEstablecimientos` (ABC) con dos adaptadores:

- `RepositorioParquet` — desarrollo y notebooks, lee `data/processed/`
- `RepositorioPostgres` — producción, consulta `hechos.v_ordenamiento_intragrupo`

**Consecuencia.** El servicio pide `repositorio.obtener(rbd, periodo)` y deja de saber si
detrás hay un archivo o una base de datos. Habilita además dobles de prueba sin tocar disco,
que es la condición para que las pruebas unitarias corran en una máquina recién clonada donde
`data/` está excluido de git.

**Costo.** Una capa de indirección más y dos implementaciones que mantener sincronizadas.

---

### P3 · Template Method — *ingesta de las 12 fuentes*

**Fuerza observada.** `quanta/q1_ingesta/fuentes.py` declara 12 fuentes como datos inertes;
el comportamiento vive disperso en 10 notebooks. El esqueleto es **idéntico en todas**:

```
localizar archivos → leer con RBD como texto → normalizar la llave →
aplicar cuarentena → escribir parquet → emitir reporte de calidad
```

Solo varía un paso: cómo se interpreta el archivo concreto (Excel con encabezado en la fila 3,
CSV latin-1 con `;`, xls antiguo). Sin abstracción, ese esqueleto se copia doce veces: es el
*pipeline jungle* que Sculley et al. describen como **"una jungla de raspados, uniones y pasos
de muestreo"**.

**Fuente.** Gamma et al. (1994): *"define el esqueleto de un algoritmo en una operación,
delegando algunos pasos a las subclases; Template Method permite que las subclases redefinan
ciertos pasos sin cambiar la estructura del algoritmo"*. Es el patrón canónico para el
principio de Hollywood ("no nos llames, nosotros te llamamos") que Freeman et al. (2004)
desarrollan en su capítulo homónimo.

**Definicion canonica.** Freeman et al. (2020, cap. 8, p. 289) definen Template Method como el
patron que *"define el esqueleto de un algoritmo en un metodo, delegando algunos pasos a las
subclases"*, de modo que estas redefinen pasos sin alterar la estructura del algoritmo.

**Costo declarado por la fuente.** La obra advierte que puede derivar en una estructura de
herencia rigida si los pasos del algoritmo base cambian de forma drastica entre
implementaciones.

**Aplicación.** `IngestorDeFuente` (ABC) fija el método plantilla `ejecutar()` con los seis
pasos invariantes; las subclases solo implementan `_leer_archivo()` y, opcionalmente,
`_normalizar()`. Los controles CTRL-01 quedan en la clase base y **no pueden ser omitidos por
una subclase**, que es precisamente la garantía que un pipeline de datos necesita.

**Consecuencia.** Añadir la fuente número 13 significa escribir una subclase de ~15 líneas.
La validación de llave, la cuarentena y el reporte de calidad se heredan y son inviolables.

**Costo.** Herencia, no composición. Se acepta conscientemente porque el esqueleto es
genuinamente fijo por normativa de ingesta y porque la alternativa —inyectar seis funciones—
sería más ceremonia para el mismo resultado.

---

### P4 · Specification — *reglas de cuarentena y de alerta*

**Fuerza observada.** Dos cadenas de condicionales que crecen con cada requisito nuevo:

1. `quanta/q1_ingesta/calidad.py` — las reglas de cuarentena (RBD ausente, año ausente, llave
   duplicada) son `if` encadenados. Faltan por incorporar: fuera de ventana temporal, ficha no
   respondida, establecimiento estructuralmente exento de medición.
2. `quanta/q3_servicio/servicios/motor.py` — `evaluar_alertas()` acumula seis condicionales
   para tres tipologías. La meta declarada es ≥ 3 tipologías, pero el diseño debe admitir más
   sin convertirse en una función de 200 líneas.

**Fuente.** Evans (2003) y Evans y Fowler (2002) definen la especificación como aquello que
*"separa el enunciado de los requisitos de los objetos evaluados"*, encapsulando una prueba
booleana `esSatisfechaPor(candidato)`. Documentan tres usos —**validación, selección y
construcción bajo pedido**— y la composición mediante `and`, `or` y `not`. Aquí se usan los
dos primeros: validación en la cuarentena, selección en las alertas.

**Aplicación.** `Especificacion` (ABC) con `es_satisfecha_por()` y los combinadores `Y`, `O`,
`NO`. Las reglas de cuarentena pasan a ser objetos nombrados y componibles; las de alerta,
subclases de `ReglaDeAlerta`.

**Consecuencia arquitectónica.** Es la respuesta directa al principio CACE. Una regla
normativa deja de ser una rama dentro de una función y pasa a ser **un objeto con nombre,
prueba unitaria propia y trazabilidad a la norma que la origina**. Cuando el MINEDUC cambia un
criterio, se modifica o se añade una especificación: el resto del flujo no se entera.

**Costo.** Más clases pequeñas. Es el intercambio clásico del patrón y aquí se paga con gusto,
porque cada regla gana una prueba unitaria aislada.

---

### P5 · Decorator — *auditoría y caché de inferencias*

**Fuerza observada.** CTRL-05 exige que **cada estimación emitida sea trazable**: persistir
modelo, versión de datos, entrada y valor en `modelos.inferencia`. Si esa responsabilidad se
escribe dentro de `EstrategiaDesagregada` y de `EstrategiaGlobal`, se duplica en ambas y se
volverá a duplicar en cada arquitectura futura. Peor: mezcla la responsabilidad de *predecir*
con la de *auditar*, violando la responsabilidad única.

**Fuente.** Gamma et al. (1994): *"adjunta responsabilidades adicionales a un objeto de forma
dinámica; los decoradores ofrecen una alternativa flexible a la herencia para extender la
funcionalidad"*. Freeman et al. (2004) lo presentan como la aplicación canónica del principio
abierto/cerrado.

**Definicion canonica.** Freeman et al. (2020, cap. 3, p. 91) definen Decorator como el patron
que *"adjunta responsabilidades adicionales a un objeto de forma dinamica, ofreciendo una
alternativa flexible a la herencia para extender funcionalidad"*.

**Costo declarado por la fuente.** La obra advierte sobre la proliferacion de clases pequenas
(p. 101), riesgo que en Q2 debe vigilarse porque el motor ya combina dos decoradores sobre la
misma estrategia.

**Aplicación.** Dos decoradores que envuelven cualquier `EstrategiaPredictiva`:

- `EstrategiaAuditada` — registra cada inferencia (CTRL-05)
- `EstrategiaConCache` — memoiza por RBD y periodo, relevante porque el cálculo de Shapley
  exacto es caro y el simulador lo invoca repetidamente

Se componen: `EstrategiaConCache(EstrategiaAuditada(EstrategiaDesagregada()))`.

**Consecuencia.** La auditoría se activa o desactiva por configuración, sin tocar el motor.
Las estrategias siguen sabiendo únicamente de matemática.

**Costo.** La cadena de decoradores puede volverse opaca al depurar. Se mitiga con
`describir()`, que expone la composición completa.

---

### P6 · Factory Method — *construcción de estrategias*

**Fuerza observada.** `quanta/q2_modelamiento/fabrica.py` resuelve estrategias con un `dict`
a nivel de módulo y una función con `lru_cache`. Funciona, pero no permite construir
estrategias **decoradas** según configuración, ni registrar arquitecturas desde fuera del
módulo.

**Fuente.** Gamma et al. (1994): *"define una interfaz para crear un objeto, pero deja que
las subclases decidan qué clase instanciar"*. En su forma de registro es lo que Fowler (2002)
llama Registry: *"un objeto bien conocido que otros objetos pueden usar para encontrar objetos
y servicios comunes"*.

**Definicion canonica.** Freeman et al. (2020, cap. 4, p. 134) definen Factory Method como el
patron que *"define una interfaz para crear un objeto, pero deja que las subclases decidan que
clase instanciar"*, difiriendo la instanciacion a las subclases.

**Costo declarado por la fuente.** La obra senala que puede obligar a crear una subclase por
cada tipo de objeto, con el consiguiente crecimiento de la jerarquia.

**Aplicación.** `FabricaDeEstrategias` con registro dinámico y armado de la cadena de
decoradores según `.env`. Se conserva `obtener_estrategia()` como función de conveniencia
para no romper el código existente.

**Costo.** Bajo. Es formalizar lo que ya existía.

---

### P7 · Facade — *fachada del motor hacia HTTP*

**Fuerza observada.** `quanta/q3_servicio/servicios/motor.py` (175 líneas, el módulo más
grande del backend) ya cumple la función de fachada: traduce entre el subsistema de
modelamiento y los esquemas HTTP. Pero al ser un módulo de funciones no puede recibir sus
dependencias por constructor, y por tanto no es sustituible en pruebas.

**Fuente.** Gamma et al. (1994): *"proporciona una interfaz unificada a un conjunto de
interfaces de un subsistema; Facade define una interfaz de más alto nivel que hace al
subsistema más fácil de usar"*.

**Definicion canonica.** Freeman et al. (2020, cap. 7, p. 264) definen Facade como el patron
que *"proporciona una interfaz unificada a un conjunto de interfaces de un subsistema,
definiendo una interfaz de nivel superior que lo hace mas facil de usar"*.

**Aplicación.** `ServicioDePrediccion(estrategia, repositorio, reglas_de_alerta)`. Los routers
la reciben por inyección de dependencias de FastAPI.

**Consecuencia.** Las pruebas de aceptación pueden inyectar un motor falso y ejercitar la API
completa sin cargar 210 MB de artefactos.

---

### P8 · Builder — *escenarios contrafactuales*

**Fuerza observada.** En `desagregada.py:simular()` y en el router de explicabilidad, los
escenarios se construyen con `escenario = dict(base); escenario[variable] = valor` repartido
en tres lugares. El simulador debe permitir modificar **varias** palancas a la vez (la meta
declarada es ≥ 4 factores simulables), y la construcción manual no escala ni valida.

**Fuente.** Gamma et al. (1994): *"separa la construcción de un objeto complejo de su
representación, de modo que el mismo proceso de construcción pueda crear representaciones
distintas"*.

**Definicion canonica.** Freeman et al. (2020, apendice, p. 614) definen Builder como el patron
que encapsula la construccion de un producto complejo y permite construirlo paso a paso.

**Costo declarado por la fuente.** La obra reconoce que anade ceremonia al codigo y exige una
logica de construccion dedicada, lo que incrementa la complejidad de la interfaz de creacion.

**Aplicación.** `ConstructorDeEscenario` con interfaz fluida:

```python
escenario = (ConstructorDeEscenario.desde(observacion)
             .con("simce_mate_4b", 290)
             .incrementar("tasa_aprobacion", 0.03)
             .construir())
```

Valida que la variable exista y que el valor caiga en rango antes de construir.

**Consecuencia.** La construcción de escenarios queda en un solo lugar, validada y probada.

---

### P9 · Virtual Proxy / Lazy Load — *artefactos de 60 MB*

**Fuerza observada.** `modelo_EFECTIVR.joblib` pesa 60,1 MB y `modelo_global_RF_comparacion.joblib`
62,1 MB. Cargar los nueve artefactos al arrancar la API costaría cientos de MB de memoria y varios
segundos, cuando una petición típica usa uno o dos. Hoy la carga diferida existe **de manera
implícita** mediante `lru_cache` y comprobaciones `if self._modelo is None`.

**Fuente.** Gamma et al. (1994) describen el *virtual proxy* como aquel que *"crea objetos
costosos bajo demanda"*. Fowler (2002) lo formaliza como Lazy Load: *"un objeto que no
contiene todos los datos que necesitas, pero sabe cómo obtenerlos"*.

**Definicion canonica.** Freeman et al. (2020, cap. 11, p. 460) definen Proxy como el patron
que *"proporciona un sustituto o marcador de posicion de otro objeto para controlar el acceso a
el"*.

**Por que la variante Virtual y no otra.** La obra cataloga un conjunto amplio de variantes
—remoto, de proteccion, entre otras (p. 488)—. Se selecciono deliberadamente la variante
virtual porque la fuerza del sistema no es el control de acceso ni la comunicacion remota, sino
el costo de creacion: diferir la carga permite que el servicio responda a las comprobaciones de
salud antes de materializar ningun artefacto.

**Aplicación.** `ArtefactoDiferido`, que expone la misma superficie que el modelo real y
materializa la deserialización en el primer `predict()`. Registra además el tiempo de carga,
insumo directo para el presupuesto de latencia que el plan de pruebas de integración exige.

**Consecuencia.** Arranque de la API en tiempo constante, independiente del tamaño del registro.

---

> **Nota de nivel.** El mismo mecanismo que aquí se describe como Registry más Factory Method
> corresponde, a nivel de estilo arquitectónico, a un **microkernel** (Richards y Ford, 2020,
> cap. 12, p. 150): un núcleo que resuelve componentes enchufables por clave. Los dos niveles
> describen la misma estructura con vocabularios distintos; el desarrollo del estilo está en
> `docs/arquitectura/ARQUITECTURA_AD_HOC.md`, sección 3.bis.

### P10 · Registry — *catálogo de factores y de modelos*

**Fuerza.** Las ponderaciones oficiales y los metadatos de modelos se consultan desde varios
puntos. Sculley et al. advierten sobre la *deuda de configuración*: **"el número de líneas de
configuración puede superar con creces al del código tradicional, y cada línea es una
oportunidad de error"**.

**Fuente.** Fowler (2002), Registry.

**Aplicación.** `RegistroDeModelos` como clase, con el catálogo de factores ya externalizado
en `contratos/catalogo_factores.json` y su tabla espejo `catalogo.factor`.

**Nota de diseño.** Registry es un Singleton disfrazado y comparte sus riesgos. Se mitiga
permitiendo instanciarlo con una ruta alternativa, de modo que las pruebas usen un registro
temporal en vez del global.

---

### P11 · Adapter — *implementaciones de los puertos hexagonales*

**Fuerza.** El estilo hexagonal adoptado exige que cada puerto tenga adaptadores
intercambiables. Sin ellos el puerto es decorativo.

**Fuente.** Gamma et al. (1994): *"convierte la interfaz de una clase en otra interfaz que
los clientes esperan"*. Cockburn (2005) lo sitúa como la pieza externa de la arquitectura
hexagonal.

**Definicion canonica.** Freeman et al. (2020, cap. 7, p. 243) definen Adapter como el patron
que *"convierte la interfaz de una clase en otra interfaz que los clientes esperan, permitiendo
que colaboren clases que de otro modo no podrian por incompatibilidad de interfaces"*.

**Costo declarado por la fuente.** La obra reconoce que introduce una capa adicional de
indireccion en la comunicacion entre objetos.

**Aplicación.**

| Puerto | Adaptadores |
|--------|-------------|
| `RepositorioEstablecimientos` | `RepositorioParquet`, `RepositorioPostgres` |
| `RegistroDeModelos` | `RegistroEnDisco` (futuro: `RegistroEnS3`) |
| `LectorDeFuente` | `LectorExcel`, `LectorCsv` |

---

### P12 · Pipes and Filters — *el flujo de ingesta*

**Fuerza.** El ETL es una secuencia de transformaciones sobre un flujo, donde cada etapa
consume la salida de la anterior. Nombrarlo permite razonar sobre reordenamiento, paralelismo
y puntos de control intermedios.

**Fuente.** Buschmann et al. (1996) lo catalogan como patrón arquitectónico; Richards y Ford
(2020) lo tratan en su estilo *pipeline architecture*.

**Aplicación.** Es el patrón arquitectónico que da forma al método plantilla de P3: cada paso
del esqueleto es un filtro, y los *checkpoints* intermedios en `data/interim/` son las tuberías
materializadas que permiten auditar el flujo por etapa.

---

## 3. Patrones evaluados y descartados

La disciplina de un catálogo de patrones se demuestra tanto por lo que se rechaza como por lo
que se adopta.

| Patrón | Por qué se consideró | Fuerza que exige la fuente | Por qué se descarta |
|--------|----------------------|----------------------------|---------------------|
| **Singleton** | El registro de modelos y el catálogo son globales de facto | Una sola instancia con punto de acceso global (cap. 5, p. 177) | Gamma et al. lo incluyen, pero la crítica posterior es sólida: introduce estado global y dificulta las pruebas. Se logra el mismo efecto con `lru_cache` **e** inyección opcional, que sí es testeable |
| **Composite** | El motor desagregado compone seis modelos en un índice | Componer objetos en estructuras de árbol y tratar de forma uniforme objetos individuales y composiciones (cap. 9, p. 356) | La composición no es recursiva ni uniforme: nunca se anida un índice dentro de otro. Aplicarlo daría estructura sin ganancia. La suma ponderada es una fórmula legal, no un árbol |
| **Observer** | Las alertas parecen notificaciones | Dependencia uno-a-muchos con notificación automática a los suscriptores (cap. 2, p. 51) | No hay publicador ni suscriptores con ciclo de vida propio: las alertas se calculan bajo demanda dentro de una petición HTTP. Especificación es el ajuste correcto |
| **Chain of Responsibility** | Las reglas de alerta se evalúan en secuencia | Pasar la petición por una cadena hasta que un manejador la atienda (p. 616) | La cadena detiene el recorrido en el primer manejador que atiende; aquí **todas** las reglas deben evaluarse. Sería usar el patrón contra su intención |
| **Abstract Factory** | Podría producir familias de estrategia + explicador + preprocesador | Crear familias de productos relacionados sin especificar sus clases concretas (p. 156) | Solo existe una familia coherente. Se reevaluará si aparece un segundo conjunto (por ejemplo, un motor para educación de adultos con normativa distinta) |
| **Command** | Cada simulación se registra en `app.simulacion` | Reificar la petición como objeto, habilitando colas, registro y deshacer (p. 206) | Registrar no es lo mismo que reificar. No hay deshacer, ni cola, ni reintento. El registro se resuelve con el decorador de auditoría |
| **Memento** | Comparar escenarios simulados | Capturar y externalizar el estado interno de un objeto para restaurarlo después (p. 624) | El escenario ya es un objeto de valor inmutable producido por el Builder; conservarlo no requiere un patrón adicional |
| **Flyweight** | Miles de establecimientos en memoria | Compartir estado intrínseco para sostener un gran volumen de objetos finos (p. 618) | El volumen (7.754 establecimientos) no justifica compartir estado intrínseco. Optimización prematura |
| **Unit of Work** | Coordinar escrituras transaccionales | — No pertenece a Head First Design Patterns; procede de Fowler (2002) | **Aplazado, no descartado.** Adquiere sentido cuando `modelos.inferencia` y `app.simulacion` se escriban en la misma transacción. Hoy no hay escrituras concurrentes |
| **Active Record** | Simplificaría el acceso a datos | — No pertenece a Head First Design Patterns; procede de Fowler (2002) | Acopla el dominio al esquema relacional. Con la persistencia en formato largo y las clases de dominio en representación ancha, el desajuste objeto-relacional es real: Data Mapper vía Repository es la elección correcta |
| **MVC / MVVM** | Organizar el frontend | Organizar interfaces complejas separando modelo, vista y control (p. 526) | React con estado local resuelve las tres ventanas. Introducir un gestor de estado global sería ceremonia para un prototipo de tres pantallas |
| **Circuit Breaker** | Resiliencia ante fallos externos | — No pertenece a Head First Design Patterns; procede de la literatura de resiliencia | No hay llamadas a servicios externos en tiempo de ejecución. La ingesta es estática y bianual |

---

La columna central es el contraste que hace verificable cada descarte: enfrenta la fuerza que la
fuente declara necesaria contra lo que ocurre en el sistema. Tres de los doce no figuran en
Head First Design Patterns y se marcan como tales, para no atribuir a esa obra una autoridad que
no tiene sobre ellos.

---

## 4. Diagrama de relaciones entre patrones

```
                    ┌─────────────────────────────────────────┐
                    │            CUANTO 1 · Ingesta           │
                    │                                         │
                    │  IngestorDeFuente  ◄── TEMPLATE METHOD   │
                    │       │                                 │
                    │       ├── LectorExcel  ◄── ADAPTER       │
                    │       ├── LectorCsv                      │
                    │       └── usa ► Especificacion           │
                    │                    ◄── SPECIFICATION     │
                    │            (PIPES AND FILTERS)           │
                    └────────────────────┬────────────────────┘
                                         │ parquet
                    ┌────────────────────▼────────────────────┐
                    │          CUANTO 2 · Modelamiento         │
                    │                                          │
                    │  EstrategiaPredictiva ◄── STRATEGY       │
                    │       ▲          ▲                        │
                    │       │          └── EstrategiaAuditada   │
                    │       │              EstrategiaConCache   │
                    │       │              ◄── DECORATOR        │
                    │       │                                   │
                    │  FabricaDeEstrategias ◄── FACTORY METHOD  │
                    │  RegistroDeModelos    ◄── REGISTRY        │
                    │  ArtefactoDiferido    ◄── VIRTUAL PROXY   │
                    │  ConstructorDeEscenario ◄── BUILDER       │
                    └────────────────────┬─────────────────────┘
                                         │ contrato
                    ┌────────────────────▼────────────────────┐
                    │           CUANTO 3 · Servicio            │
                    │                                          │
                    │  ServicioDePrediccion ◄── FACADE         │
                    │       │                                  │
                    │       └── RepositorioEstablecimientos    │
                    │              ◄── REPOSITORY (puerto)     │
                    │                 ├── RepositorioParquet   │
                    │                 └── RepositorioPostgres  │
                    │                     ◄── ADAPTER          │
                    │           ReglaDeAlerta ◄── SPECIFICATION│
                    └────────────────────┬─────────────────────┘
                                         │ HTTP/JSON
                    ┌────────────────────▼────────────────────┐
                    │            CUANTO 4 · Cliente            │
                    │        (sin patrones de dominio)         │
                    └──────────────────────────────────────────┘
```

**Lectura del diagrama.** Los patrones no se distribuyen al azar: **los creacionales y
estructurales se concentran en Q2**, donde vive la complejidad algorítmica y los artefactos
costosos; **los de comportamiento en Q1 y Q3**, donde viven las reglas de negocio que cambian
por normativa. El cuanto 4 no tiene patrones de dominio porque no debe tener dominio: es un
adaptador de presentación.

---


### Combinación de patrones y riesgo de saturación

Freeman et al. (2020, cap. 12) advierten sobre la *fiebre de patrones*: la tendencia a introducir
estructura por afinidad técnica y no por necesidad, con el resultado de que la sinergia entre
patrones aumenta la complejidad en lugar de contenerla. La interacción que se observa en Q2 entre
Strategy, Decorator, Factory Method y Registry —una fábrica que produce estrategias decoradas y
las resuelve desde un registro— corresponde a una combinación análoga a las que la propia obra
documenta.

**La fuente no proporciona ningún criterio numérico para determinar cuándo un sistema tiene
demasiados patrones.** No existe un umbral publicado contra el cual contrastar los doce que este
catálogo declara, y conviene no inventar uno.

Lo que sí puede argumentarse es de naturaleza estructural, no cuantitativa: los doce patrones no
conviven en un mismo espacio de nombres sino distribuidos entre cuatro unidades de despliegue
independiente con alta cohesión interna. Esa partición actúa como aislamiento de complejidad. La
fiebre de patrones degrada un sistema cuando la estructura de un módulo obliga a entender la de
los demás para modificar cualquiera; aquí el grafo de dependencias entre cuantos está restringido
y verificado por máquina, de modo que la complejidad introducida en Q2 no se propaga a Q1, Q3 ni
Q4. La concentración es además deliberada y asimétrica: seis de los doce patrones viven en Q2,
que es donde reside la complejidad algorítmica y los artefactos costosos, mientras que Q4 no
aplica ninguno de dominio.

En consecuencia, la cifra por sí sola no permite concluir sobre saturación. Lo que la haría
observable es otra cosa: que una modificación en un cuanto obligue a tocar otro. Ese es el
indicador que corresponde vigilar, y hoy la verificación de fronteras lo mantiene acotado.

---

## 5. Trazabilidad con los controles de arquitectura

| Control | Patrón que lo materializa | Cómo |
|---------|---------------------------|------|
| CTRL-01 · Orfandad de llaves | **Specification** + **Template Method** | Las reglas de cuarentena son objetos componibles y el esqueleto de ingesta impide omitirlas |
| CTRL-02 · Fuga de datos | **Template Method** | La verificación anti-fuga es un paso invariante de la clase base |
| CTRL-03 · Deriva de datos | **Registry** | La línea base se versiona junto a los metadatos del modelo |
| CTRL-04 · Acceso no autorizado | **Facade** | El servicio exige jurisdicción antes de delegar en el motor |
| CTRL-05 · Trazabilidad | **Decorator** | `EstrategiaAuditada` persiste toda inferencia sin contaminar el motor |

---

## 6. Consecuencias medibles

Medido end-to-end contra el modelo real `modelo_global_INDICER.joblib` (1,43 MB) con
scikit-learn 1.5.2 y el conjunto `tabla_modelo_largo.parquet` (23.111 observaciones):

| Métrica | Antes | Después | Medición |
|---------|-------|---------|----------|
| Módulos de la capa de servicio que conocen el formato de almacenamiento | 1 | 0 | `scripts/verificar_arquitectura.py` |
| Reglas de negocio con prueba unitaria aislada | 0 | 9 | 26 pruebas en `tests/unitarias/q2/test_patrones_del_motor.py` |
| Líneas para incorporar una fuente nueva | ~120 (notebook completo) | ~15 (una subclase) | Revisión de código |
| Estrategias que deben implementar la auditoría | cada una | 0 (la aporta el decorador) | `test_decorador_de_auditoria_registra_sin_tocar_la_estrategia` |
| Artefactos materializados al arrancar la API | potencialmente 9 (210 MB) | **0** | `GET /api/v1/salud/registro` → `n_materializados: 0` |
| Latencia de una predicción repetida | 2.548 ms | **0,09 ms** | Decorador de caché, factor 29.844× |
| Coste de carga diferido fuera del arranque | — | 2,50 s | `ArtefactoDiferido.segundos_de_carga` |
| Pruebas totales de la suite | 18 | **44** | `pytest -q` |

### Dos hallazgos que la implementación destapó

**1. Desajuste entre entrenamiento y servicio.** El repositorio apuntaba primero a
`tabla_entrenamiento_modelo.parquet`, que tiene 29 columnas y solo 13 de las 65 variables que
el modelo global exige. El conjunto correcto es `tabla_modelo_largo.parquet` —23.111
observaciones, la misma cifra que declara `metadatos_modelo_global.json`—. Corregido el orden
de candidatos, la cobertura sube a **57 de 65 variables (88 %)**.

Las 8 restantes son las diferencias SIMCE entre bienios (`dif_simce_*`), que **se calculan
dentro del notebook de entrenamiento y no se persisten**. Hoy se imputan por mediana: la
predicción funciona, pero se degrada en silencio. `ServicioDePrediccion.diagnostico_de_cobertura()`
vuelve observable ese desajuste y lo expone en `GET /api/v1/salud/composicion`. La solución de
fondo —materializar las variables derivadas en la capa de persistencia— queda como deuda
declarada, no como sorpresa.

**2. Acoplamiento de versión en los artefactos.** Los `.joblib` se serializaron con scikit-learn 1.6.1 y el entorno de servicio fija 1.5.2
(`AttributeError: _RemainderColsList`). Requieren la versión con la que fueron entrenados, que
es la fijada en `requirements.txt` (1.5.2). Refuerza el argumento de CTRL-05: los metadatos del
registro deben incluir la versión de la librería, no solo los hiperparámetros.

---

## Referencias

- Buschmann, F., Meunier, R., Rohnert, H., Sommerlad, P. y Stal, M. (1996). *Pattern-Oriented
  Software Architecture, Volume 1: A System of Patterns*. Wiley.
- Cockburn, A. (2005). *Hexagonal Architecture (Ports and Adapters)*.
- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*.
  Addison-Wesley.
- Evans, E. y Fowler, M. (2002). *Specifications*. https://martinfowler.com/apsupp/spec.pdf
- Ford, N., Richards, M., Sadalage, P. y Dehghani, Z. (2021). *Software Architecture: The Hard
  Parts*. O'Reilly.
- Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.
  Catálogo en línea: https://martinfowler.com/eaaCatalog/
- Freeman, E., Robson, E., Bates, B. y Sierra, K. (2020). *Head First Design Patterns* (2.a ed.).
  O'Reilly Media.
- Gamma, E., Helm, R., Johnson, R. y Vlissides, J. (1994). *Design Patterns: Elements of
  Reusable Object-Oriented Software*. Addison-Wesley.
- Richards, M. y Ford, N. (2020). *Fundamentals of Software Architecture*. O'Reilly.
- Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V.,
  Young, M., Crespo, J.-F. y Dennison, D. (2015). Hidden Technical Debt in Machine Learning
  Systems. *Advances in Neural Information Processing Systems 28*.
  https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf
