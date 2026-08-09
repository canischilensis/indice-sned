# Informe del Hito 2 — Planificación, Alcance y Propuesta de Solución

**Proyecto de Título — Ecosistema predictivo del Índice SNED con Inteligencia Artificial Explicable**

| | |
|---|---|
| **Autor** | Guillermo Vidal Astudillo |
| **Profesor guía** | Jerry Peña · **Jefatura de carrera:** Félix Burgos |
| **Carrera** | Ingeniería en Informática — Universidad Andrés Bello |
| **Repositorio** | `indice-sned` (público) · **Fecha de entrega:** 9 de agosto de 2026 |

---

## Índice

**Introducción** · **1. Tópicos del plan de proyecto** (1.1 Justificación metodológica · 1.2 Gestión · 1.3 Desarrollo · 1.4 Alcance · 1.5 Cronograma · 1.6 Calidad · 1.7 Riesgos · 1.8 Cambios · 1.9 Comunicaciones) · **2. Alcance del proyecto** (2.1 Las causas del problema · 2.2 Criterio de intervención · 2.3 Qué hace el software · 2.4 Límites · 2.5 Exclusiones técnicas) · **3. Propuesta de solución** (3.1 Diagrama de contexto · 3.2 Controles operacionales · 3.3 Funcionamiento macro · 3.4 Cobertura) · **4. Plan de proyecto** (4.1 Etapas · 4.2 Programación y estimación · 4.3 Instancias de control · 4.4 Depuración de situaciones) · **5. Propuesta de extensión (fuera de alcance)** · **Conclusiones** · **Referencias**

**Figuras.** 1 Diagrama de contexto (§3.1) · 2 Arquitectura hexagonal (§3.3) · 3 Vista de despliegue (§3.3) · 4 Patrones por cuanto (§3.3) · 5 Secuencia de predicción (§3.3) · 6 Secuencia de simulación (§3.3) · 7 Secuencia de explicabilidad (§3.3) · 8 Modelo entidad-relación (§3.3) · 9 Modelo físico (§3.3).

**Tablas.** 1 Comparación metodológica (§1.1) · 2 Modelo de calidad (§1.6) · 3 Riesgos estructurales (§1.7) · 4 Configuración controlada y cambios prohibidos (§1.8) · 5 Ishikawa: las causas del problema (§2.1) · 6 Controles operacionales (§3.2) · 7 Frontera de información por factor (§3.3) · 8 Trazabilidad causa–componente–objetivo–control (§3.4) · 9 Carta Gantt (§4.2) · 10 Hitos de control (§4.3) · 11 Depuración de situaciones (§4.4).

---

# Introducción

El Sistema Nacional de Evaluación de Desempeño asigna cada dos años una Subvención por Desempeño de Excelencia a los establecimientos subvencionados mejor evaluados dentro de su Grupo Homogéneo. El beneficio tiene consecuencia monetaria directa, pero su mecánica resulta opaca: seis factores con ponderaciones normativas, calculados sobre información dispersa en portales estatales desconectados y resueltos por posición relativa dentro de un grupo cuya composición cambia entre ciclos. El efecto es una gestión reactiva, en la que el equipo directivo conoce el desenlace con el ciclo ya cerrado y sin poder atribuir la pérdida a ningún indicador.

El proyecto responde con un ecosistema predictivo que estima el índice y sus seis factores desde datos públicos, explica cada estimación a nivel de establecimiento mediante inteligencia artificial explicable y permite simular el efecto de mover variables de gestión antes del corte. Una premisa gobierna el diseño: el sistema asiste la decisión directiva, no la sustituye.

A la fecha el sistema está construido y operativo: once fuentes públicas de cuatro organismos, sesenta y cinco variables, 23.111 observaciones sobre 7.754 establecimientos, tres arquitecturas comparadas bajo validación cruzada agrupada por RBD, una base PostgreSQL de treinta y ocho tablas en cuatro esquemas y un prototipo B2B de tres ventanas. Los diagramas se derivaron del código escrito, no de un diseño previo. El informe se organiza según los cuatro criterios de la rúbrica y añade una quinta sección fuera del alcance comprometido.

---

# 1. Tópicos del plan de proyecto

## 1.1 Justificación de la elección metodológica

La gestión se rige por Scrum (Schwaber y Sutherland, 2020) por tres fuerzas concretas del proyecto, no por preferencia.

La primera es la **incertidumbre del dato público**: al iniciar no se sabía qué contenían las once fuentes ni con qué cobertura, y era imposible predecir el comportamiento de la llave estricta RBD más año sin haber ejecutado la ingesta. El **modelo en cascada**, cuyo riesgo en sistemas complejos advirtió Royce (1970), habría fijado requisitos sobre datos cuya existencia era aún una hipótesis, incurriendo en lo que Goodpasture (2016) llama planificación a distancia; la experiencia lo confirmó, porque la depuración del universo y el hallazgo de llaves huérfanas ocurrieron durante la ejecución. La segunda es el **plazo trimestral fijo**: **Kanban** visualiza el flujo continuo (Anderson, 2010), pero sin límites temporales carece del mecanismo que obliga a converger dentro de un trimestre académico. La tercera es que **el proyecto no termina en un modelo entrenado**: **CRISP-DM** organiza el ciclo de minería (Chapman et al., 2000), pero no gobierna un servicio con control de acceso, una interfaz de gestión ni una base auditable, que son tres de los seis bloques de trabajo. Se descartó también la vía híbrida, que habría añadido costo de coordinación sin beneficio para un equipo de una persona.

**Tabla N° 1. Comparación metodológica y justificación de la elección**

| Criterio | Cascada | CRISP-DM | Kanban | Scrum (seleccionado) |
|---|---|---|---|---|
| Naturaleza | Secuencial y rígida | Proceso de minería de datos | Flujo continuo sin límite temporal | Iterativo e incremental, iteraciones acotadas |
| Requisitos | Cerrados al inicio | Evolutivos, solo sobre el dato | Evolutivos, sin compromiso acotado | Evolutivos, con compromiso por iteración |
| Incertidumbre del dato público | Nula: exige conocer el dato antes de tocarlo | Parcial: la absorbe en el dato, no en el producto | Alta, sin convergencia forzada | Alta: cada iteración incorpora lo descubierto |
| Convergencia en un trimestre | Sin control intermedio | No aplica | Ausente | Cinco cierres con criterio verificable |
| Gobierna servicio y persistencia | Sí | No | Parcialmente | Sí |
| Validación del avance | Por fase terminada | Por fase de minería | Por tarjeta movida | **Por cumplimiento verificable de sprint** |
| Veredicto | Descartada | Descartada | Descartada | **Adoptada** |

## 1.2 Metodología de gestión

El *Product Backlog* concentra requisitos y hallazgos pendientes. El *Sprint Backlog* recoge el compromiso semanal y controla el trabajo simultáneamente en curso, previniendo cuellos de botella y desperdicio por multitarea. El *Incremento* es el resultado verificable de cada iteración, y su condición de terminado no se declara: se comprueba contra la definición del plan de calidad. El *Daily Scrum* controla el flujo diario; el *Sprint Review* es el hito formal donde el avance validado se contrasta contra la carta Gantt; y la *Retrospectiva* registra lo aprendido, instancia donde se documentaron varios de los hallazgos de la sección 4.4. Esa triangulación permite detectar desviaciones temprano.

## 1.3 Metodología de desarrollo del software

Opera un modelo **incremental e iterativo con compuerta de calidad por incremento**: un incremento no se integra por estar terminado, sino por superar tres barreras en orden estricto. La primera comprueba código y estructura de datos —análisis estático, tipos, integridad del esquema, fronteras entre cuantos y auditoría anti-fuga—. La segunda evalúa los criterios de aceptación mediante la suite, con una regla sin excepción: un fallo del control de acceso reprueba la barrera completa. La tercera aplica solo si el incremento toca el modelo, y exige superioridad sostenida mediante intervalos de confianza y prueba t pareada; un R² mayor por sí solo no basta. Si alguna falla, el incremento retorna al backlog y se preserva la última versión estable de los artefactos.

El mecanismo sustituye a la revisión por pares que un equipo mayor tendría: con un solo desarrollador, la disciplina debe trasladarse a comprobaciones que una máquina ejecute y que no puedan omitirse por conveniencia. El trabajo se organizó por **cuantos de arquitectura y no por capas técnicas**, de modo que cada incremento entregara valor demostrable por sí mismo.

## 1.4 Gestión del alcance

El producto comprometido estima el índice y sus seis factores desde datos públicos, explica cada estimación, permite simular escenarios y expone todo mediante un servicio con control de acceso y una interfaz. El sistema **asiste**: no reemplaza la decisión, no calcula el beneficio monetario oficial y no sustituye acto administrativo alguno. La descomposición se organizó en seis bloques —ingesta y calidad; modelamiento y explicabilidad; servicio; interfaz de gestión; persistencia relacional; aseguramiento y documentación—, con paquetes cuyo criterio de terminación es una comprobación. El plan registra siete criterios de aceptación, todos cumplidos, entre ellos que el índice reconstruido coincida con el oficial dentro de una milésima y que las fronteras de arquitectura se verifiquen por máquina sin violaciones.

El control de la deriva opera con cuatro preguntas en orden, donde la primera negativa detiene el análisis: si responde a un objetivo declarado, si puede verificarse, si es compatible con las restricciones de diseño y si cabe en el plazo sin degradar lo construido. Lo que no las supera se registra como trabajo futuro, categoría con siete elementos vigentes.

## 1.5 Gestión del cronograma

El cronograma abarca **cinco iteraciones semanales entre el 15 de julio y el 18 de agosto de 2026** y se planificó **por dependencias técnicas y no por duración estimada**: no era posible estimar el modelamiento sin haber ejecutado la ingesta, porque la matriz de entrenamiento es producto de esta última. La regla derivada es que ningún incremento comienza antes de que su predecesor supere la compuerta de calidad. La programación detallada se desarrolla en la sección 4.

## 1.6 Gestión de la calidad

El plan se estructura sobre ISO/IEC 25010 para el producto y sobre ISO/IEC/IEEE 29119 para el proceso de prueba. Tres reglas lo gobiernan: la calidad se verifica y no se declara; el criterio no se ajusta para que una prueba apruebe; y lo que no se cumple se declara.

**Tabla N° 2. Modelo de calidad: métricas, umbrales y estado verificado**

| Característica (ISO/IEC 25010) | Métrica | Umbral | Estado verificado |
|---|---|---|---|
| Adecuación funcional · corrección | Discrepancia del índice reconstruido frente al oficial | ≤ 0,001 | Cumple: máx. 0,0006 · media 0,00025 · 44.679 filas |
| Adecuación funcional · completitud | Requisitos funcionales con verificación | 100 % | Cumple: 13 de 13 |
| Eficiencia de desempeño | Latencia de operaciones de lectura | < 1 s | Cumple, con dos excepciones declaradas |
| Compatibilidad · interoperabilidad | Conformidad con el esquema publicado | 100 % de las rutas del cliente | Cumple |
| Fiabilidad · madurez | Suite en verde en cada envío | 100 % | Cumple: 61 pruebas |
| Seguridad · confidencialidad | Accesos fuera de jurisdicción | 0 | Cumple |
| Mantenibilidad · modularidad | Violaciones del grafo de dependencias | 0 | Cumple, verificado por máquina |
| Mantenibilidad · testabilidad | Suite ejecutable sin base ni artefactos | Sí | Cumple |
| Portabilidad · adaptabilidad | Adaptadores intercambiables con equivalencia demostrada | ≥ 2 | Cumple: 141 llamadas, 0 divergencias |

La **calidad del dato** es dimensión propia porque el sistema estima sobre información pública incompleta. La integridad referencial se resuelve con cuarentena en ingesta y claves foráneas en persistencia, con cero huérfanos persistidos; la unicidad, con llaves primarias compuestas; la cobertura de llave se exige sobre 0,95 y, de no alcanzarse, se reporta. La completitud se declara en lugar de rellenarse: **si una fuente no cubre a un establecimiento, esa fila no existe**. El 68,8 % de ausentes estructurales en las columnas de segundo medio es un hallazgo sobre la publicación estatal, no un defecto a maquillar.

La **calidad del modelo** se declara con igual franqueza. El motor global alcanza R² de 0,637 y el desagregado 0,583, frente a un umbral comprometido de 0,60; el que alimenta el simulador es el desagregado y no lo alcanza. El incumplimiento queda visible en lugar de rebajarse la meta: corresponde declarar umbrales diferenciados, porque los dos motores no responden la misma pregunta —uno estima mejor, el otro dice qué mover—.

## 1.7 Gestión de riesgos

Se distinguen los riesgos estructurales, propios del dominio, de los de proceso. A cada riesgo estructural se le asignó un control verificable, con la numeración que desarrolla la sección 3.2.

**Tabla N° 3. Riesgos estructurales: cualificación, materialización y mitigación**

| Riesgo | Prob. | Impacto | Materialización | Mitigación |
|---|---|---|---|---|
| Orfandad de llaves e integridad referencial | Alta | Alto | **Se materializó**: registros sin correspondencia al empalmar | CTRL-01 · cuarentena en lugar de descarte y claves foráneas hacia el catálogo |
| Fuga del objetivo hacia las variables de entrada | Alta | Crítico | Prevenido | CTRL-02 · exclusión estructural, partición agrupada y predictor trivial |
| Deriva de datos por ruptura postpandemia | Media | Alto | Confirmada como fenómeno del dominio | CTRL-03 · verificación bianual contra línea base |
| Pérdida de trazabilidad estimación–artefacto | Media | Alto | Prevenido | CTRL-05 · registro versionado con metadatos |

Tres riesgos de proceso se materializaron: la incompletitud de las fuentes, que produjo el 68,8 % de ausentes y se respondió con formato largo, banderas de ausencia y cuarentena; el acoplamiento de los artefactos a la versión de la biblioteca con que fueron entrenados, serializados con la 1.6.1 mientras el entorno de servicio fija la 1.5.2, desalineación medida y declarada como deuda; y **la prueba que no prueba nada**, pues la suite de paridad aprobó tres veces sin comparar nada real, porque contrastaba dos respuestas de error, dos listas vacías y dos esquemas sin restricciones. Ese hallazgo documenta un modo de fallo que ninguna métrica de cobertura detecta.

## 1.8 Gestión de cambios

El plan existe porque hay elementos cuya modificación **invalida resultados ya reportados** sin que ninguna prueba lo advierta. Sin procedimiento, esa invalidación ocurre en silencio.

**Tabla N° 4. Elementos bajo control de configuración y cambios prohibidos**

| Elemento bajo control | Efecto de un cambio no controlado | Cambio prohibido sin autorización |
|---|---|---|
| Esquema de base de datos | Rompe la carga y altera la precisión de lo persistido | Modificarlo para acomodar el catálogo en archivo: el esquema es la fuente de verdad |
| Vista materializada de entrenamiento | Cambia la población y todas las métricas reportadas | Alterar su unión |
| Catálogo de ponderaciones | Cambia todo índice reconstruido | Usar los seis factores, el índice o la agrupación como variable de entrada |
| Contratos de los puertos | Rompe simultáneamente todos los adaptadores | Eliminar el adaptador de archivos columnares: sin él no hay paridad que verificar |
| Contrato público de la interfaz | Rompe el cliente | Persistir columnas derivadas |
| Artefactos de modelo | Cambia las estimaciones servidas | Sobrescribir artefactos o archivos de origen |
| Criterios de comparación de las pruebas | Hace aprobar una suite que debería fallar | Relajar el criterio para que una prueba apruebe |
| Documentos de línea base | Desalinea la trazabilidad | Refactorizar código para que un diagrama quede más limpio |

Los cambios se clasifican en **menores** (no alteran contratos, esquema ni resultados; proceden directo), **mayores** (alteran un contrato o el comportamiento observable; exigen evaluación de impacto escrita) y **críticos** (pueden invalidar resultados reportados; exigen además reejecutar todas las verificaciones afectadas). El registro consigna seis cambios ya aplicados: cuatro críticos, uno mayor y uno menor, retomados en la sección 4.4.

## 1.9 Gestión de comunicaciones

El plan identifica seis interesados con su necesidad y frecuencia: el profesor guía requiere avance verificable y decisiones fundamentadas, por hito; la comisión evaluadora, que el sistema exista, funcione y esté justificado, en la defensa; el equipo directivo, saber qué mover y cuánto confiar, en cada uso; el sostenedor, la situación comparada de su red, en cada uso; el auditor, poder verificar el cálculo, bajo demanda; y el desarrollador futuro, retomar el sistema sin arqueología, de forma permanente. Para este último, nueve preguntas previsibles están mapeadas al documento que las responde.

El aporte del plan es tratar **la interfaz como canal formal**, con siete requisitos verificables: la incertidumbre acompaña a la estimación en la misma tarjeta mediante el error medio; lo acotado por información no publicada se distingue por color y por una columna de restricción; el alcance se declara al pie de las tres vistas; la posición real se distingue de lo simulado mediante un punto de referencia sobre la curva; la explicación declara su validez mediante la tarjeta de aditividad; la ausencia de dato se nombra —"sin medición de"— en lugar de mostrarse como cero; y el error del servicio se muestra sin suavizar, de modo que si se consulta un establecimiento ausente de la base analítica, la interfaz lo dice. Cinco limitaciones se comunican cuantificadas: el 63 % de ponderación acotada, el menor poder explicativo del motor desagregado, la cobertura de variables del 81,4 %, los 4,6 segundos de la simulación y el mayor costo del ordenamiento intragrupo.

---

# 2. Alcance del proyecto

## 2.1 Las causas del problema central

El problema central se enuncia así: los sostenedores y equipos directivos no pueden anticipar ni explicar la obtención o pérdida de la Subvención por Desempeño de Excelencia, lo que los condena a una gestión reactiva sobre un beneficio de alto impacto financiero e institucional. Sobre ese enunciado se identificaron dieciséis causas distribuidas en cuatro categorías, provenientes de la literatura revisada, del registro técnico del desarrollo y de una entrevista semiestructurada con un usuario objetivo real.

**Tabla N° 5. Diagrama de Ishikawa: las causas del problema central por categoría**

| N° | Causa | Efecto e incidencia en el problema central |
|---|---|---|
| **A · Datos e Información** | | |
| A1 | Fuentes públicas dispersas en portales asíncronos y desconectados | Obliga a consolidación manual sin formato ni periodicidad comunes; impide una visión unificada antes del corte |
| A2 | Orfandad de la llave integradora RBD más año | Deja registros huérfanos al empalmar; fragmenta la base analítica e invalida el cálculo de los afectados |
| A3 | Registros históricos de rendimiento publicados sin clasificación | Exige una fase completa de depuración; imposibilita el uso directo por el establecimiento, sin capacidad técnica |
| A4 | Ficha del instrumento: microdatos no publicados y de autorreporte no fiscalizable | El 11 % de la ponderación depende de un instrumento no auditable; techo infranqueable a la reconstrucción externa |
| **B · Metodología de Evaluación del Estado** | | |
| B1 | Los puntajes brutos confunden calidad institucional con nivel socioeconómico | Produce comparaciones injustas; impide interpretar la posición real frente a pares comparables |
| B2 | Trampa de la superación: mantener buenos resultados no otorga el beneficio | Deja fuera a establecimientos con desempeño alto y estable; pérdida sin deterioro pedagógico atribuible |
| B3 | Escalamiento relativo nacional | Mejoras propias significativas rinden incrementos marginales; distorsiona la expectativa de retorno |
| B4 | Ruptura metodológica postpandemia | Las series dejan de ser comparables linealmente; invalida la proyección por tendencia y confunde lo exógeno con la gestión |
| B5 | Ausencia de instrumento específico de medición del buen trato y la convivencia | Dimensiones trabajadas no se reflejan en el índice; desalinea el esfuerzo institucional respecto de lo evaluado |
| **C · Capacidad Técnica del Establecimiento** | | |
| C1 | Ausencia de herramientas predictivas al alcance del establecimiento | El diagnóstico depende de la intuición directiva; impide anticipar con base en evidencia |
| C2 | Procesos manuales lentos de consolidación | El análisis llega tras el cierre del ciclo; anula el margen de reacción sobre variables aún modificables |
| C3 | Imposibilidad de atribuir la pérdida a indicadores específicos | El resultado llega como cifra agregada sin descomposición causal; impide focalizar recursos |
| **D · Gestión y Planificación Institucional** | | |
| D1 | Gestión reactiva | La intervención ocurre sobre un ciclo cerrado; convierte la planificación en administración de crisis |
| D2 | Variables silenciosas: indicadores de desarrollo personal, sanciones y mediaciones | Penalizaciones normativas no anticipadas; erosionan el índice por vías ajenas al desempeño académico |
| D3 | Ausencia de hoja de ruta plurianual hacia la excelencia | Las actividades se presupuestan aisladas; dispersa el recurso y diluye su efecto sobre el resultado |
| D4 | Dificultad para sostener la excelencia una vez obtenida | El establecimiento desconoce qué condiciones mantener; transforma el logro en un evento no reproducible |

## 2.2 El criterio de intervención informática

El criterio aplicado, formulado para poder contrastarse causa por causa, es el siguiente: **una causa es abordable por medios informáticos cuando su origen está en la incapacidad de procesar información que existe y está disponible; no lo es cuando depende del diseño del instrumento evaluativo estatal.**

La distinción es operativa. Las causas de la categoría A, salvo A4, describen información que existe pero que ningún establecimiento puede consolidar por falta de capacidad técnica: son problemas de procesamiento, y el procesamiento es precisamente lo que un sistema informático hace. Las de la categoría C describen la ausencia de la herramienta misma, de modo que construirla las resuelve por definición. Las de la categoría D describen decisiones de gestión tomadas a ciegas por falta de información oportuna y descompuesta, carencia subsanable mediante estimación anticipada y atribución por variable. Las de la categoría B son mixtas: B1, B2 y B4 son consecuencias de la metodología estatal que **pueden modelarse** porque sus insumos son públicos, mientras que B3 y B5 dependen del diseño del instrumento.

A4 y B5 describen decisiones de diseño del instrumento estatal, no limitaciones de procesamiento. Ningún recurso algorítmico puede reconstruir un instrumento que no se publica y que además se autodeclara sin fiscalización, ni suplir una dimensión que el índice no mide. Pretender lo contrario no sería ambición técnica sino error de categoría, y produciría un sistema que aparenta cubrir lo que no cubre.

## 2.3 Qué hace el software con cada causa abordada

La integración de las once fuentes mediante ingestores propios bajo la llave RBD más año resuelve la dispersión (A1); la validación estricta de la llave compuesta, con derivación a cuarentena, resuelve la orfandad (A2); y la depuración y normalización de los registros históricos resuelve la falta de estructura (A3). El consumo directo de los Grupos Homogéneos oficiales, sin recalcular la agrupación, neutraliza el sesgo de los puntajes brutos (B1); el modelo desagregado del factor Superación, con simulación contrafactual, aborda la trampa de la superación (B2); y la programación de las excepciones normativas —exclusión de la medición estandarizada de 2022 y ausencia de mediciones en 2020 y 2021— junto con la verificación empírica de la ventana congelada absorbe la ruptura postpandemia (B4).

El prototipo de tres ventanas es en sí mismo la herramienta predictiva ausente (C1); la automatización del flujo elimina los procesos manuales lentos (C2); y la atribución de Shapley con verificación de aditividad resuelve la imposibilidad de atribución (C3). La estimación anticipada antes del corte revierte la gestión reactiva (D1); la incorporación de indicadores de desarrollo personal y social, denuncias, sanciones y mediaciones como predictoras hace visibles las variables silenciosas (D2); el reporte con horizonte bienal ordena la hoja de ruta (D3); y el monitoreo de la posición intragrupo con simulación de escenarios de mantención aborda la dificultad de sostener la excelencia (D4). La correspondencia completa se demuestra en la Tabla N° 8.

## 2.4 Los límites del alcance

**A4 — Ficha del instrumento, no publicada y de autorreporte no fiscalizable.** Los microdatos que alimentan los factores Iniciativa e Integración, equivalentes al 11 % de la ponderación, no se publican, y el instrumento es de autodeclaración sin fiscalización, extremo confirmado en terreno por el usuario entrevistado. Ninguna solución externa puede reconstruir un instrumento que no existe públicamente y cuya validez interna no es auditable.

**B5 — Convivencia sin instrumento específico.** El índice no incorpora un instrumento que mida el buen trato y la convivencia como dimensión propia. El proyecto integra los indicadores de desarrollo personal y social que sí se publican, pero no puede suplir una dimensión que el instrumento no mide.

**B3 — Escalamiento relativo nacional, abordable de forma parcial.** El resultado depende del desempeño del conjunto del sistema, condición que ningún establecimiento controla. El proyecto no la elimina: la hace explícita. El simulador comunica la magnitud realista del efecto de cada movimiento, evitando la sobreventa. El punto se convirtió en hallazgo propio: un movimiento de 83 puntos en una medición estandarizada, del orden de dos desviaciones estándar respecto de la media nacional, equivale a solo 2,24 puntos de índice.

Las tres delimitaciones se fundan en la **frontera de información irreducible**: cinco de los seis factores, equivalentes al **63 % de la ponderación**, dependen de datos que solo obran en poder del Estado. El sistema propaga esa frontera hasta la interfaz mediante un campo que viaja en cada respuesta y se renderiza como distinción visual, de modo que la limitación es parte del producto y no una nota al pie.

## 2.5 Exclusiones técnicas

La **orquestación de operaciones de aprendizaje automático** se descarta porque el fenómeno se calcula cada dos años y el reentrenamiento continuo sería deuda técnica desproporcionada a ese ciclo; se sustituye por serialización versionada, cuadernos de verificación reproducible y control de versiones. El **agrupamiento algorítmico para reconstruir los Grupos Homogéneos** se descarta porque el Estado los publica: recalcularlos introduciría discrepancia con el cálculo oficial sin ganancia. El **tratamiento de datos personales** se excluye por privacidad, mediante omisión total de identificadores individuales. Los **establecimientos no académicos regulares** quedan fuera por no ser comparables bajo la mecánica del índice. El plan de alcance registra otras cuatro exclusiones de producto: el cálculo del monto del beneficio, la administración de usuarios por interfaz, la alta disponibilidad de la base y la aplicación móvil nativa.

---

# 3. Propuesta de solución

## 3.1 Diagrama de contexto y flujos con control

El ecosistema se organiza en cuatro etapas encadenadas. La figura las presenta e identifica, sobre cada flujo, el control operacional que allí interviene. Rotular **flujos y no componentes** es deliberado: un control declarado a nivel de módulo no es verificable, mientras que uno situado sobre un flujo se comprueba observando lo que ese flujo produce.

![Figura N° 1](docs/diagramas/06_contexto.png)

**Figura N° 1.** *Diagrama de contexto: cuatro etapas y los flujos con control operacional.* Elaboración propia. CTRL-01, CTRL-02, CTRL-03 y CTRL-05 aparecen sobre más de un flujo: no son puntos únicos sino condiciones sostenidas a lo largo de la cadena. CTRL-03, el único capaz de detener el avance, se representa como nodo transversal con arista de retorno.

La **primera etapa** son los sistemas de origen: el Ministerio de Educación aporta cinco fuentes —resultados oficiales del índice, rendimiento, matrícula, subvención escolar preferencial y dotación—; la Agencia de Calidad de la Educación, dos —mediciones estandarizadas e indicadores de desarrollo personal y social—; la Superintendencia de Educación, tres —procesos administrativos, denuncias y mediaciones—; y la Junta Nacional de Auxilio Escolar y Becas, el índice de vulnerabilidad. El catálogo declara una duodécima fuente, referida a desvinculación, evaluada y descartada porque no permite atribución por RBD: queda registrada como descartada, no como omisión.

La **segunda etapa** es la capa analítica, donde ocurre la normalización bajo la llave estricta RBD más año con exclusión total de identificadores personales. **CTRL-01 opera sobre el flujo de la ingesta hacia el conjunto analítico** y, en su segunda manifestación, sobre el de la base relacional hacia la ingeniería de características, donde la integridad se refuerza con las veintisiete claves foráneas que cruzan esquemas. El conjunto se materializa en archivos columnares en formato largo y se carga de forma idempotente en la base.

La **tercera etapa** es el motor predictivo. **CTRL-02 opera en dos flujos consecutivos**: el que alimenta la ingeniería de características, impidiendo que los seis factores, el índice oficial o la agrupación ingresen como entrada, y el que va de las características al entrenamiento, donde impone la partición agrupada por RBD y la ventana temporal. **CTRL-05 opera sobre el flujo que deposita los artefactos en el registro** y sobre el de carga diferida hacia el servicio. **CTRL-03 opera transversal y bianualmente** sobre dos flujos: la lectura de distribuciones desde la base y la habilitación o detención del reentrenamiento.

La **cuarta etapa** es la capa de servicio B2B: la interfaz de programación expone predicción, alertas, explicación por Shapley, evaluación de escenarios, curva de sensibilidad y posición intragrupo, y **CTRL-04 opera sobre el flujo del servicio hacia el cliente**, restringiendo cada consulta a los establecimientos bajo la jurisdicción del usuario autenticado.

## 3.2 Tabla de controles operacionales

**Tabla N° 6. Controles operacionales del ecosistema**

| ID | Riesgo mitigado | Flujo donde se implementa | Descripción técnica del funcionamiento | Evidencia que genera |
|---|---|---|---|---|
| **CTRL-01** | Orfandad de llaves e integridad referencial | Ingesta → conjunto analítico; base → características | Cada registro se evalúa contra reglas de admisión componibles construidas sobre el puerto `Especificacion[T]`: validez del identificador y del año, unicidad de la llave compuesta y pertenencia a la ventana temporal. Los no conformes se derivan a cuarentena en lugar de descartarse, y permanecen como evidencia. En persistencia, la integridad se refuerza con veintisiete claves foráneas hacia el catálogo, sin referencias laterales entre esquemas | Archivos de cuarentena por fuente y reporte de calidad con cobertura de llave; umbral ≥ 0,95 y, si no se alcanza, reporte explícito |
| **CTRL-02** | Fuga del objetivo hacia las variables de entrada | Conjunto analítico → características → entrenamiento | Verificación de que los seis factores, el índice oficial y la agrupación no figuran entre las entradas; su presencia levanta una excepción de fuga que detiene el proceso. El particionamiento se ejecuta agrupado por RBD, de modo que un establecimiento no aparezca a la vez en entrenamiento y prueba. La restricción temporal es ventana declarada en el esquema, no un comentario en un script. El resultado se contrasta contra un predictor trivial | Excepción de fuga registrada y R² del predictor trivial próximo a cero, comprobado en el cuaderno de entrenamiento |
| **CTRL-03** | Deriva de datos por la ruptura postpandemia | Verificación bianual: base → contraste → entrenamiento | Contraste de la distribución vigente contra la línea base registrada al entrenar. Un desplazamiento significativo en variables de peso alto obliga a reentrenar; su ausencia obliga a no hacerlo, porque reentrenar sin señal introduce variación sin ganancia. Es el único control capaz de detener la publicación de un modelo | Registro de contraste en la tabla de deriva. **Pendiente declarado:** la línea base de distribuciones aún no ha sido generada |
| **CTRL-04** | Accesos no autorizados fuera de jurisdicción | Servicio → cliente | Toda ruta que recibe un identificador de establecimiento exige jurisdicción antes de tocar la persistencia. La respuesta ante un establecimiento ajeno es negativa de autorización y nunca de recurso inexistente, de modo que el sistema no filtra por omisión la existencia de establecimientos ajenos. La interfaz refuerza el control: el selector se alimenta solo de los identificadores del token, sin campo de texto libre | Respuestas de denegación registradas y pruebas automatizadas de control de acceso; un fallo reprueba la barrera de calidad completa |
| **CTRL-05** | Pérdida de trazabilidad estimación–artefacto | Entrenamiento → registro → inferencia | Los artefactos se serializan junto a metadatos que declaran variables de entrada, hiperparámetros y métricas. El servicio los materializa por carga diferida en la primera petición que los exija, y toda inferencia servida puede asociarse a la versión que la produjo | Artefactos versionados con metadatos y esquema de registro de inferencias y atribuciones. **Pendiente declarado:** las tablas de inferencia están creadas y aún no reciben escrituras |

Dos observaciones cierran la tabla. **Dos de los cinco controles declaran evidencia que todavía no se genera**, y ello se consigna en lugar de omitirse: el rigor de un plan de controles se mide por su honestidad sobre lo que aún no ejerce. Y los controles no son documentación: tres de los cinco se verifican automáticamente en cada ejecución de la suite, y el grafo de dependencias entre cuantos se comprueba mediante un script que recorre las importaciones reales y retorna error si alguna sale del grafo permitido.

## 3.3 Funcionamiento a nivel macro

### Arquitectura: puertos, adaptadores y cuantos

El sistema adopta una **arquitectura hexagonal de puertos y adaptadores** (Cockburn, 2005), particionada en cuatro cuantos: ingesta, modelamiento, servicio y cliente. La elección proviene de cuatro fuerzas del dominio: la consecuencia monetaria exige auditabilidad; la volatilidad normativa exige que las reglas cambiantes queden tras abstracciones; la necesidad del directivo de saber qué mover exige que la explicabilidad sea núcleo y no anexo; y la periodicidad bianual justifica excluir la orquestación de aprendizaje automático.

![Figura N° 2](docs/diagramas/01_hexagonal.png)

**Figura N° 2.** *Arquitectura hexagonal: los cuatro puertos y sus adaptadores.* Elaboración propia, derivada del código real. Cada puerto aísla exactamente una dimensión de cambio: esa correspondencia uno a uno distingue una abstracción necesaria de una indirección gratuita.

Los cuatro puertos son `Especificacion[T]`, que aísla las reglas de negocio volátiles por normativa y se implementa tanto en las reglas de admisión de ingesta como en las de alerta del servicio; `IngestorDeFuente`, que aísla formato y codificación de cada fuente, con adaptadores para hoja de cálculo y para archivos delimitados en dos codificaciones; `EstrategiaPredictiva`, que aísla el algoritmo tras las tres operaciones de predecir, explicar y simular; y `RepositorioEstablecimientos`, que aísla el medio de persistencia con dos adaptadores intercambiables por configuración.

Sobre el despliegue corresponde una precisión expresa: **los cuatro cuantos son lógicos; las unidades de despliegue son tres.** La ingesta se ejecuta como proceso por lotes independiente y el cliente se compila a archivos estáticos, de modo que ambos son cuantos físicos; el modelamiento y el servicio comparten proceso y binarios y conforman un único cuanto físico, con forma de monolito modular (Richards y Ford, 2020). Es deliberado: la comunicación síncrona entre servicio y motor es un requisito de latencia del simulador, y separarlos introduciría coordinación de despliegue y latencia de red para resolver un problema de escalabilidad que este sistema, de baja concurrencia y ciclo bianual, no tiene.

![Figura N° 3](docs/diagramas/06_despliegue.png)

**Figura N° 3.** *Vista de despliegue: cuatro cuantos lógicos, tres unidades de despliegue.* Elaboración propia. La separación del código no implica separación del proceso.

### Patrones de diseño y estilos internos

El sistema aplica doce patrones y descarta explícitamente otros doce, cada uno con la fuerza que lo justifica y su fuente citada (Gamma et al., 1994; Freeman et al., 2020).

![Figura N° 4](docs/diagramas/02_patrones.png)

**Figura N° 4.** *Patrones de diseño aplicados por cuanto.* Elaboración propia, derivada del código real. Se concentran donde residen la complejidad algorítmica y los artefactos costosos; el cliente no aplica ninguno de dominio, porque incorporar allí lógica de negocio duplicaría la regla.

Tres patrones sostienen la propuesta. **Strategy** encapsula el motor tras un contrato único, verificado empíricamente al comparar tres arquitecturas algorítmicas sobre idéntica representación de entrada sin modificar una línea de la capa de servicio. **Repository** aísla el medio de persistencia mediante una fábrica que resuelve el adaptador por clave de configuración. **Decorator** añade auditoría y memorización sin alterar la estrategia base. Cada cuanto aplica además un estilo interno distinto: **tubería y filtros** en la ingesta, **capas cerradas** en el servicio —ninguna ruta alcanza la persistencia sin atravesar la fachada— y **microkernel** en el modelamiento, donde un registro explícito resuelve estrategias por clave.

### Flujos principales

![Figura N° 5](docs/diagramas/03_secuencia_prediccion.png)

**Figura N° 5.** *Secuencia de predicción del índice y sus seis factores.* Elaboración propia, derivada del código real. La verificación de jurisdicción antecede a todo acceso a la persistencia: una consulta no autorizada no llega a tocar el dato.

![Figura N° 6](docs/diagramas/04_secuencia_simulacion.png)

**Figura N° 6.** *Secuencia de simulación de escenarios.* Elaboración propia, derivada del código real. Nueve puntos de malla por seis modelos producen cincuenta y cuatro inferencias por llamada, del orden de 4,6 segundos; la memorización no ayuda porque cada punto es una observación distinta.

![Figura N° 7](docs/diagramas/05_secuencia_shap.png)

**Figura N° 7.** *Secuencia de explicabilidad y carga diferida de artefactos.* Elaboración propia, derivada del código real. La materialización ocurre en la primera solicitud de explicación, no al construir el objeto: el servicio responde a las comprobaciones de salud sin haber cargado los 210 MB del registro.

Las latencias medidas completan el cuadro: autenticación bajo 50 milisegundos, predicción bajo 300, listado bajo 200 y explicación por Shapley bajo 500. Las dos excepciones —declaradas y no resueltas— son la simulación, con 4,6 segundos, y el ordenamiento intragrupo, dos veces y media más lento sobre la base relacional porque recalcula funciones de ventana sobre 54.298 filas por consulta. La explicabilidad incorpora además la verificación de **aditividad**: la suma de las contribuciones más el valor base debe reproducir la predicción dentro de una milésima, y el resultado viaja hasta la interfaz. Una explicación que no verifica su aditividad es una ilustración plausible, no una descomposición.

**Tabla N° 7. Frontera de información irreducible por factor**

| Factor | Ponderación | R² alcanzado | Restricción de información |
|---|---|---|---|
| Efectividad | 37 % | 0,832 | Ninguna |
| Superación | 28 % | 0,200 | Corrección por significancia estadística no publicada |
| Igualdad de oportunidades | 22 % | 0,128 | Subtipo de sanción por discriminación no desagregado |
| Iniciativa | 6 % | 0,084 | Ficha de autorreporte no pública |
| Integración | 5 % | 0,132 | Ficha de autorreporte no pública |
| Mejoramiento | 2 % | 0,024 | Varianza del objetivo próxima a cero |

El único factor sin restricción concentra el 37 % de la ponderación y alcanza R² de 0,832; los cinco restantes, que suman el 63 %, operan sobre información acotada. Eso explica el desempeño agregado.

### Persistencia

![Figura N° 8](docs/diagramas/00_modelo_entidad_relacion.png)

**Figura N° 8.** *Modelo entidad-relación.* Elaboración propia. Las mediciones y los resultados son entidades débiles: dependen existencialmente del establecimiento y del periodo, y eso determina la estructura de llaves del modelo físico.

![Figura N° 9](docs/diagramas/00_modelo_fisico_bd.drawio.png)

**Figura N° 9.** *Modelo físico de la base de datos.* Elaboración propia. Las veintisiete claves foráneas que cruzan esquemas —dieciocho desde hechos, cinco desde el registro de modelos, cuatro desde la operación— apuntan todas hacia el catálogo: topología de estrella.

La base comprende **38 tablas en cuatro esquemas** —dieciséis de catálogos y dimensiones, seis de hechos, ocho de registro de modelos y ocho de operación—, con aproximadamente 838.000 filas; veintiuna derivan del modelo entidad-relación y el resto es infraestructura. El esquema responde a seis decisiones de normalización, cada una anclada a un hallazgo medido: formato largo para mediciones e indicadores, por el 68,8 % de ausentes estructurales; Grupo Homogéneo indexado por periodo, porque el 35,1 % de los establecimientos cambia de agrupación entre ciclos; ponderaciones como dato de catálogo, con la fórmula oficial verificada de forma exacta; dimensión de cambio lento para atributos que varían por ciclo, como la migración de dependencia hacia los servicios locales sin cambio de RBD; ventanas temporales declaradas en el esquema y no en un script; y una tabla genérica de indicadores anuales que permite añadir una fuente insertando registros. Un disparador diferido verifica al cierre de cada transacción que la suma de ponderaciones sea exactamente la unidad.

Tres vistas de consumo completan el diseño: la reconstrucción del índice como consulta auditable, el ordenamiento intragrupo y la matriz de entrenamiento materializada. La primera sostiene la propiedad más importante del sistema: **el índice oficial se reconstruye desde el dato persistido sin ejecutar código de aplicación**, con discrepancia máxima de 0,0006 y media de 0,00025 sobre 44.679 establecimientos. El residuo corresponde al redondeo de la publicación oficial a tres decimales, no a error del modelo.

### Interfaz de programación y cliente

El servicio expone catorce rutas versionadas. Ocho son de negocio: listado de establecimientos bajo jurisdicción, detalle, posición dentro del Grupo Homogéneo, predicción del índice y sus factores, alertas tipificadas, explicación por Shapley, curva de sensibilidad y evaluación de escenarios. Las seis restantes cubren autenticación, identidad del usuario, tres comprobaciones de salud y composición, y el catálogo de ponderaciones. Todas las que reciben un identificador de establecimiento exigen jurisdicción antes de acceder al dato, conforme a CTRL-04.

El prototipo consta de tres ventanas más la pantalla de acceso. El **tablero** presenta la estimación con su error medio en la misma tarjeta, el motor activo con su versión, el desglose de los seis factores con distinción visual de los acotados, la tabla de factor, peso, valor, aporte y restricción, y el panel de alertas con severidad. El **simulador** presenta la curva de expectativa condicional individual sobre cinco palancas, con el punto de posición real diferenciado del trazado simulado, la verificación de monotonicidad y la advertencia de magnitud realista. El **reporte de explicabilidad** descompone cada factor en contribuciones por variable ordenadas por magnitud, declara la aditividad y nombra las ausencias de dato como tales.

*Nota sobre las capturas:* el documento de diseño de interfaz especifica siete capturas del sistema definitivo con sus nombres de archivo, contenido y procedimiento —incluida la condición de capturar a un ancho no inferior a 1.280 píxeles—. **El directorio correspondiente no existe aún en el repositorio**, de modo que las ventanas se describen textualmente y las capturas quedan pendientes.

## 3.4 Demostración de cobertura

**Tabla N° 8. Trazabilidad: causa, componente que la mitiga, objetivo específico y control**

| Causa | ¿Abordada? | Componente concreto que la mitiga | O.E. | Control |
|---|---|---|---|---|
| A1 · Fuentes dispersas | Sí | Integración de once fuentes mediante ingestores propios bajo llave RBD más año | 1 | — |
| A2 · Orfandad de llaves | Sí | Validación estricta de la llave compuesta con cuarentena y auditoría posterior | 1 y 2 | CTRL-01 |
| A3 · Registros sin clasificar | Sí | Depuración y normalización de los registros históricos de rendimiento | 2 | CTRL-01 |
| A4 · Ficha no pública | **No abordable** | Fuera de alcance por diseño: frontera de información irreducible | — | — |
| B1 · Puntajes brutos sesgados | Sí | Consumo directo de los Grupos Homogéneos oficiales, sin recalcular la agrupación | 3 | — |
| B2 · Trampa de la superación | Sí | Modelo desagregado del factor Superación y simulación contrafactual | 4 | CTRL-02 |
| B3 · Escalamiento relativo | **Parcial** | El simulador comunica la magnitud realista del efecto y evita la sobreventa | 4 | — |
| B4 · Ruptura postpandemia | Sí | Excepciones normativas programadas y verificación de la ventana congelada | 3 | CTRL-03 |
| B5 · Convivencia sin instrumento | **No abordable** | Depende del diseño del instrumento evaluativo estatal | — | — |
| C1 · Sin herramientas predictivas | Sí | Prototipo B2B de tres ventanas funcionales | 4 y 5 | CTRL-04 |
| C2 · Procesos manuales lentos | Sí | Automatización del flujo de ingesta, depuración y consolidación | 1 y 2 | CTRL-01 |
| C3 · Pérdida no atribuible | Sí | Atribución de Shapley con verificación de aditividad | 5 | CTRL-05 |
| D1 · Gestión reactiva | Sí | Estimación anticipada antes del corte oficial del ciclo | 4 y 5 | CTRL-02 |
| D2 · Variables silenciosas | Sí | Indicadores de desarrollo personal, denuncias, sanciones y mediaciones como predictoras | 3 | CTRL-01 |
| D3 · Sin hoja de ruta plurianual | Sí | Reporte con horizonte bienal alineado al ciclo real del índice | 5 | — |
| D4 · Dificultad para sostener la excelencia | Sí | Monitoreo de la posición intragrupo y simulación de escenarios de mantención | 5 | CTRL-04 |

El proyecto aborda **trece causas de forma directa**, **una de forma parcial** (B3) y **dos quedan explícitamente fuera** (A4 y B5) con fundamento en la frontera de información. La cobertura es completa dentro del dominio de lo abordable. La trazabilidad no se agota aquí: el repositorio mantiene una matriz que encadena cada uno de los trece requisitos funcionales con su caso de uso, componente de diseño, unidad de código y prueba, con tres requisitos declarados sin cobertura automatizada y su motivo consignado.

---

# 4. Plan de proyecto

## 4.1 Etapas de gestión y de desarrollo

El plan ejecutable se organiza en cinco fases, cada una coincidente con un sprint semanal y con un entregable verificable al cierre.

La **fase de depuración** aborda los registros históricos de rendimiento publicados sin clasificar, define criterios de exclusión trazables y establece el universo de establecimientos sobre el que operará todo lo demás. La **fase de integración** ejecuta la ingesta de las fuentes estatales, valida la llave estricta RBD más año y deriva a cuarentena los registros no conformes. La **fase de preparación** construye la ingeniería de características sobre las sesenta y cinco variables, consume los Grupos Homogéneos oficiales y diseña el esquema normalizado con su carga idempotente y su verificación del cálculo. La **fase de modelamiento** entrena las tres arquitecturas bajo validación cruzada agrupada por RBD e implementa la atribución de Shapley y las curvas de expectativa condicional individual. La **fase de despliegue B2B** construye las tres ventanas, integra la explicabilidad y conecta el prototipo a la base.

## 4.2 Programación y estimación

**Tabla N° 9. Carta Gantt de los cinco sprints y su alcance por paquete de trabajo**

| Sprint | Fechas | Fase | Paquetes comprometidos | Entregable verificable al cierre |
|---|---|---|---|---|
| 1 | 15 – 21 jul 2026 | Depuración histórica | Caracterización de las once fuentes; criterios de exclusión trazables | Conjunto depurado con criterios documentados |
| 2 | 22 – 28 jul 2026 | Integración e ingesta | Ingestores por formato y codificación; reglas de admisión y cuarentena; reportes de calidad | Once fuentes normalizadas, con cuarentena y reporte por fuente |
| 3 | 29 jul – 4 ago 2026 | Preparación y persistencia | Matriz de entrenamiento; modelo E-R y físico; 38 tablas; vistas de reconstrucción y ordenamiento; carga idempotente | Base cargada y verificada: discrepancia del índice ≤ 0,001 |
| 4 | 5 – 11 ago 2026 | Modelamiento y explicabilidad | Protocolo anti-fuga; motor global y desagregado; Shapley; simulación; registro de artefactos | Motor dual entrenado con aditividad verificada |
| 5 | 12 – 18 ago 2026 | Despliegue B2B | Interfaz versionada; autenticación y jurisdicción; reglas de alerta; tablero, simulador y reporte XAI | Tres ventanas operando contra el servicio real y conmutación demostrada |

Sobre la **estimación de esfuerzo** corresponde una declaración explícita. **El proyecto no estimó en puntos de historia ni registró velocidad de equipo**, y la razón está documentada: con un solo desarrollador la métrica de velocidad carece de término de comparación y su cálculo produciría una cifra sin capacidad de predicción. Tampoco se estimó en horas-hombre. La base de la programación es otra: **la cadena de dependencias técnicas verificables**. Cada incremento tiene su dependencia dura declarada con motivo técnico —el modelamiento no puede empezar sin matriz normalizada; el servicio no puede encapsular un motor inexistente; la interfaz consume un contrato que debe estar publicado; la comparación entre adaptadores exige dos adaptadores operativos; y la documentación se produce al final porque los diagramas se derivan del código final, y documentar antes habría documentado un borrador—. El camino crítico atraviesa ingesta, modelamiento, servicio, conmutación y documentación; la persistencia era paralelizable en teoría, pero convergió en la conmutación y en la práctica se ejecutó después, incorporándose al camino crítico.

La consecuencia de planificar así es verificable: la interfaz quedó operativa antes de que la base existiera, consumiendo el adaptador de archivos columnares. No fue una anomalía de planificación sino la demostración temprana de que la frontera del puerto de repositorio funcionaba.

## 4.3 Instancias de control

El plan contempla tres niveles de control. El **control diario** lo ejerce el *Daily Scrum* sobre el flujo, con vigilancia del trabajo simultáneamente en curso. El **control por iteración** lo ejercen el *Sprint Review* y la *Retrospectiva*: el primero contrasta el incremento contra el compromiso y contra la carta Gantt, el segundo registra lo aprendido. **El cumplimiento verificable de sprints es el criterio de validación del avance**: el proyecto no mide progreso en porcentaje declarado, porque un incremento "al 80 %" no informa; mide hitos cerrados con su criterio cumplido. El **control de incorporación** es la compuerta de calidad con sus tres barreras en orden estricto. La definición de terminado añade dos condiciones: la documentación afectada se actualiza en el mismo cambio, y los defectos que queden abiertos se registran con su causa.

**Tabla N° 10. Hitos de control con criterio de cierre verificable**

| Hito | Criterio de cierre | Verificación efectuada | Estado |
|---|---|---|---|
| H1 · Datos normalizados | Las once fuentes producen archivos columnares con reporte de calidad y cuarentena | Reportes por fuente | Cerrado |
| H2 · Modelo entrenado y explicable | Artefactos registrados con métricas; aditividad verificada | Métricas del registro | Cerrado |
| H3 · Servicio operativo | Las funciones del catálogo responden; control de acceso probado | Suite de integración | Cerrado |
| H4 · Interfaz operativa | Las tres ventanas contra el servicio real | Verificación manual documentada | Cerrado |
| H5 · Base cargada y verificada | Índice reconstruido con discrepancia ≤ 0,001 | Máxima 0,0006 sobre 44.679 filas | Cerrado |
| H6 · Conmutación demostrada | Equivalencia campo por campo, todas las llamadas exitosas | 141 llamadas, 0 divergencias | Cerrado |
| H7 · Documentación completa | Requisitos, arquitectura, diseño, gestión, manuales y planes | Índice maestro del repositorio | Cerrado |
| H8 · Defensa | Sistema demostrable en vivo | — | Pendiente |

El avance al cierre de este hito es de siete hitos cerrados sobre ocho; trece requisitos funcionales sobre trece con verificación; cinco integraciones cubiertas sobre cinco; sesenta y una pruebas en la suite; y cuatro niveles de prueba implementados sobre seis, con aceptación y compatibilidad redactados y no implementados, ambos con su plan específico.

## 4.4 Depuración de las situaciones encontradas

Un plan que muestra cómo absorbió imprevistos reales informa más que uno que presenta un avance lineal que no ocurrió. El proyecto registra tres retrocesos que reabrieron incrementos cerrados y seis cambios clasificados y aplicados bajo el procedimiento de control de cambios.

**Tabla N° 11. Depuración de situaciones encontradas durante la ejecución**

| Situación | Cómo se detectó | Causa raíz | Resolución y verificación reejecutada | Efecto sobre el plan |
|---|---|---|---|---|
| **El motor desagregado no podía predecir** | Falló la predicción extremo a extremo al conectar el servicio | Los artefactos esperaban las banderas de ausencia; los metadatos declaraban solo las variables base | Corrección de la matriz de variables; reejecución de la predicción completa y de la aditividad. Cambio crítico | Reabrió el incremento de modelamiento y bloqueó el hito de servicio |
| **La suite de paridad aprobaba sin comparar nada** | El resumen mostraba llamadas comparadas no exitosas | Tres supuestos falsos del arnés: dos respuestas de error, dos listas vacías y dos esquemas sin restricciones | Registro de un usuario de prueba con jurisdicción real y comprobación que exige llamadas exitosas. Cambio mayor | Reabrió el hito de conmutación tres veces |
| **La precisión numérica truncaba los valores de origen** | Viaje de ida y vuelta contra el archivo de origen | La precisión decimal elegida perdía información en dos familias de tablas | Seis decimales en mediciones de desarrollo personal, verificado sobre 248.957 observaciones; ocho decimales en indicadores anuales, con error máximo de 5·10⁻⁹. Dos cambios críticos | Obligó a recargar la base completa |
| **Unidad de análisis mal fijada por cambio de Grupo Homogéneo** | Análisis exploratorio del resultado oficial por ciclo | El 35,1 % de los establecimientos cambia de agrupación entre ciclos: la agrupación es atributo del par establecimiento-periodo, no del establecimiento | Indexación del Grupo Homogéneo por periodo, con el identificador de periodo en la llave de la tabla de resultados | Determinó la segunda decisión de normalización del esquema |
| **Incompletitud estructural de las fuentes** | Reporte de calidad por fuente | El 68,8 % de ausentes en las columnas de segundo medio es propiedad de la publicación estatal | Formato largo, banderas de ausencia y cuarentena; no se imputó ninguna fila | Fijó la regla de oro del dato y una dimensión propia en el plan de calidad |
| **Traducción innecesaria de códigos entre adaptadores** | Divergencia en la suite de paridad | La diferencia era temporal, no de vocabulario | Retiro de la traducción y reejecución completa de la suite. Cambio crítico | Simplificó el adaptador relacional |
| **Identificador de demostración inexistente tras la depuración** | Prueba manual de la interfaz | El RBD fijado no sobrevivió al criterio de exclusión | Sustitución por un establecimiento del conjunto depurado, verificada manualmente. Cambio menor | Sin efecto sobre el camino crítico |

Cuatro de estas situaciones se clasificaron como cambios críticos, lo que activó la exigencia procedimental más estricta: evaluación de impacto escrita y reejecución de todas las verificaciones afectadas. Los tres retrocesos comparten un rasgo: **se corrigió la causa y no el criterio**. Alargar el cronograma para corregir la causa es el intercambio que hace que el resultado tenga valor probatorio.

El plan mantiene además cuatro riesgos de cronograma con mitigación aplicada: que una fuente pública cambie de formato o desaparezca, mitigado conservando los archivos crudos y documentando la redescarga; que un hallazgo tardío invalide resultados reportados, mitigado con verificaciones automatizadas en cada envío; que los artefactos dejen de cargar por actualización de dependencias, mitigado fijando versiones; y la pérdida del entorno, mitigada porque todo se reconstruye desde el repositorio.

---

# 5. Propuesta de extensión: agente asesor de gestión (fuera de alcance)

> **Advertencia de alcance.** Esta sección es una **propuesta de extensión** y no un desarrollo comprometido. Queda expresamente fuera del alcance del prototipo evaluado en este hito. De abordarse, se desarrollaría en una rama anexa del repositorio, `q5-agente-asesor`, separada de la línea principal. No se comprometen resultados, métricas ni fechas.

**Objetivo.** El sistema cierra la brecha entre el dato disperso y la información correcta, pero no la que va de la información a la decisión. Un equipo directivo que abre el reporte de explicabilidad encuentra la estimación, el desglose de los seis factores, las contribuciones de Shapley y la curva de sensibilidad: cifras exactas y auditables que no responden la pregunta operativa —qué mover primero, cuánto rinde moverlo y qué no vale la pena tocar—. La extensión aborda esa brecha traduciendo la explicación técnica a lenguaje natural y priorizándola.

**Ubicación arquitectónica.** El agente entraría como **quinto cuanto (Q5)** detrás de un puerto nuevo, `AsesorDeGestion`, del mismo modo en que `RepositorioEstablecimientos` gobierna hoy sus dos adaptadores. No tocaría el dominio ni las tres ventanas, y si se retirara el sistema seguiría operando. La ubicación no es estética: es la única compatible con la función de aptitud que verifica el grafo de dependencias entre cuantos, porque un componente que accediera directamente al motor o a la persistencia haría fallar esa comprobación.

**Principio rector.** El agente orquesta y traduce; el motor predictivo calcula; el equipo directivo decide. El modelo de lenguaje **no computa el índice ni pondera factores**, porque duplicaría el dominio y produciría dos implementaciones de la misma fórmula.

**Herramientas.** Tres, y las tres envuelven rutas existentes y probadas: diagnóstico, sobre la predicción y las alertas; explicación por factor, sobre la atribución de Shapley; y simulación de escenario, sobre `POST /prediccion/{rbd}/escenario`, ruta ya construida que acepta varias variables de gestión movidas simultáneamente. El agente las consultaría como cualquier usuario, sometido por tanto al mismo control de jurisdicción de CTRL-04.

**Por qué se descarta la recuperación aumentada.** El dato ya está estructurado en una base relacional normalizada y expuesto por una interfaz tipada. Fragmentar esos registros para recuperarlos por similitud semántica sería incompatible con la integridad relacional que el proyecto construyó, e introduciría riesgo de imprecisión justamente donde la consulta directa es determinística.

**Orquestación.** Un bucle de ejecución simple —el agente decide qué herramienta invocar, observa el resultado y continúa— basta como punto de partida. Escalar a planificación explícita solo se justificaría con evidencia de que la complejidad lo exige.

**Guardarraíles.** Dos restricciones gobernarían la salida. Toda cifra citada debe provenir de una respuesta de herramienta, y un validador posterior a la generación rechaza el texto si aparece un número ausente de ellas. Y no se prometen retornos: el hallazgo de que un movimiento de 83 puntos en la medición estandarizada equivale a 2,24 puntos de índice convierte esa restricción en algo medible incorporado al contrato de salida, y no en una buena intención redactada.

**Evaluación.** El conjunto de evaluación ya existe: la muestra congelada de veinte establecimientos del arnés de paridad, con semilla fija y cuatro casos borde deliberadamente incluidos —un establecimiento sin medición de segundo medio, uno rural, uno que cambia de Grupo Homogéneo entre ciclos y uno en el tramo superior del indicador socioeconómico—. Sobre ella podrían medirse, contra datos reales, la precisión del ruteo de herramienta, la exactitud de las cifras citadas y la ausencia de promesas de retorno.

**Patrones previstos.** Strategy para el puerto, Adapter por proveedor de modelo, Decorator para instrumentar consumo de tokens y costo, y Gateway para encapsular la llamada al servicio externo.

**Reevaluación que esta extensión obliga.** El repositorio descartó el patrón Circuit Breaker con un argumento explícito: no existen llamadas a servicios externos en tiempo de ejecución, porque la ingesta es estática y bianual. Con el agente ese argumento deja de ser cierto, ya que una llamada por red puede fallar o degradarse. El descarte **debe reevaluarse** antes de cualquier implementación, y esa reevaluación quedaría registrada como decisión de arquitectura.

**Por qué queda fuera del alcance comprometido.** Por alcance, porque una cuarta ventana es alcance nuevo sujeto al procedimiento de control de cambios. Por riesgo, porque incorporar una dependencia externa en tiempo de ejecución introduce un modo de fallo que el sistema actual no tiene. Y por método, porque el proyecto declaró que la calidad se verifica y no se declara, y un componente generativo cuya evaluación no se ha ejecutado no cumpliría ese estándar.

---

# Conclusiones

El proyecto llega a este hito con la planificación ejecutada, el alcance delimitado sobre un análisis causal explícito y la propuesta de solución construida y verificable.

Sobre los **tópicos del plan**, la elección de Scrum se justificó frente a alternativas concretas: la incertidumbre del dato público hacía inviable la planificación anticipada cerrada, el alcance excedía lo que CRISP-DM gobierna y el plazo trimestral hacía insuficiente un método sin límites temporales. Los ocho tópicos operan sobre mecanismos comprobables, y la compuerta de calidad por incremento sustituye a la revisión por pares que un equipo mayor tendría.

Sobre el **alcance**, la delimitación se sostiene en un criterio contrastable causa por causa: una causa es abordable cuando su origen está en la incapacidad de procesar información disponible, y no lo es cuando depende del diseño del instrumento evaluativo estatal. Trece se abordan de forma directa, una parcialmente y dos quedan fuera. La frontera de información irreducible, que alcanza al 63 % de la ponderación, es un hallazgo verificable sobre las condiciones de replicabilidad externa del cálculo estatal, y el sistema la propaga hasta la interfaz en lugar de ocultarla.

Sobre la **propuesta de solución**, los cinco controles están situados sobre flujos concretos y no sobre componentes, condición que los hace verificables, y tres se comprueban de forma automatizada en cada ejecución de la suite. La propiedad más relevante del sistema no es ninguna cifra de tamaño sino una verificación: el índice oficial se reconstruye desde el dato persistido, sin ejecutar código de aplicación, con discrepancia máxima de seis diezmilésimas sobre 44.679 establecimientos. Eso lo hace auditable y no meramente funcional.

Sobre el **plan de proyecto**, la programación por cadena de dependencias verificables resultó adecuada para un dominio de datos desconocido, y la ausencia de estimación en puntos de historia se declara con su razón en lugar de simularse. Las siete situaciones depuradas —tres retrocesos y cuatro cambios críticos— evidencian que el proceso fue iterativo y que el criterio de aceptación nunca se movió para acomodar un resultado.

Queda declarado lo que no se cumple: el motor que alimenta el simulador no alcanza el umbral comprometido, con 0,583 frente a 0,60; dos de los cinco controles declaran evidencia que aún no generan; dos limitaciones de rendimiento siguen abiertas por decisión explícita; dos de los seis niveles de prueba están redactados y no implementados; y las capturas del sistema definitivo están pendientes. Consignar esos puntos no debilita el informe: los omitiría un documento que persigue la aprobación en lugar de la exactitud.

---

# Referencias

Anderson, D. J. (2010). *Kanban: Successful evolutionary change for your technology business*. Blue Hole Press.

Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc.

Cockburn, A. (2005). *Hexagonal architecture (ports and adapters)*. https://alistair.cockburn.us/hexagonal-architecture/

Ford, N., Richards, M., Sadalage, P., & Dehghani, Z. (2021). *Software architecture: The hard parts. Modern trade-off analyses for distributed architectures*. O'Reilly Media.

Freeman, E., Robson, E., Bates, B., & Sierra, K. (2020). *Head first design patterns* (2.ª ed.). O'Reilly Media.

Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design patterns: Elements of reusable object-oriented software*. Addison-Wesley.

Goodpasture, J. C. (2016). *Project management the agile way: Making it work in the enterprise* (2.ª ed.). J. Ross Publishing.

International Organization for Standardization. (2011). *ISO/IEC 25010:2011. Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models*.

International Organization for Standardization. (2013). *ISO/IEC/IEEE 29119:2013. Software and systems engineering — Software testing*.

Kruchten, P. (1995). Architectural blueprints — The 4+1 view model of software architecture. *IEEE Software, 12*(6), 42-50. https://doi.org/10.1109/52.469759

Richards, M., & Ford, N. (2020). *Fundamentals of software architecture: An engineering approach*. O'Reilly Media.

Royce, W. W. (1970). Managing the development of large software systems. *Proceedings of IEEE WESCON*, 1-9.

Schwaber, K., & Sutherland, J. (2020). *La Guía de Scrum: La guía definitiva de Scrum — Las reglas del juego*. https://scrumguides.org/

Theza, D. (2026, 15 de abril). *Entrevista semiestructurada con usuario objetivo* [Comunicación personal].
