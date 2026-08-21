# Fuentes metodológicas oficiales del SNED

Identificador del documento: **FM-SNED-01**
Fecha de apertura: **21 de agosto de 2026**

Registro de lo que la documentación oficial **dice textualmente** sobre el cálculo del Índice
SNED, con su documento y página. Existe por una razón concreta: durante el desarrollo se
verificó que afirmaciones metodológicas dadas por sabidas no estaban respaldadas por ninguna
fuente, y que una consulta asistida podía reconstruir tablas plausibles sin advertir que las
estaba infiriendo.

**Regla de este documento.** Solo entra lo que tiene documento, página y cita textual. Lo que no
está, se declara ausente y **no se reconstruye**. Una tabla inferida que parece oficial es peor
que una ausencia declarada, porque nadie la audita.

---

## 1. Documentos disponibles y ausencias declaradas

| Ciclo | Documento técnico | Estado |
|-------|-------------------|--------|
| 2018-2019 | `Sned_20182019.pdf` | Disponible |
| 2020-2021 | — | **Ausente.** No se dispone del documento técnico oficial |
| 2022-2023 | `Documento-Tecnico-SNED-2022-2023.pdf` | Disponible |
| 2024-2025 | — | **Ausente.** No se dispone del documento técnico oficial |
| 2026-2027 | `Documento-Tecnico-SNED-2026-2027.pdf` | Disponible |

Las dos ausencias son relevantes para la tesis: **cualquier afirmación sobre las ventanas de
medición de los ciclos 2020-2021 y 2024-2025 carece hoy de respaldo documental** y debe
enunciarse como supuesto, no como hecho.

### 1.1 La reutilización de datos pre-pandemia: qué está probado y qué no

| Ciclo | Afirmación | Respaldo |
|-------|-----------|----------|
| 2022-2023 | Efectividad y Superación se calcularon con SIMCE 2017, 2018 y 8º 2019 | **Documentado.** *Documento Técnico SNED 2022-2023*, p. 8, sección I.2 |
| 2024-2025 | Reutiliza la misma matriz pre-pandemia | **No documentado.** Solo consta en registros internos del proyecto |

La cita disponible, del ciclo 2022-2023, p. 8:

> «Para el SNED 2022-2023, los factores Efectividad y Superación fueron calculados con las Pruebas
> SIMCE disponibles, es decir SIMCE 2017, SIMCE 2018 y SIMCE 8º 2019. Dado que no fue posible la
> aplicación de las pruebas para otros niveles en los años 2019 y 2020.»

**Consecuencia práctica para la tesis.** Entrenar los ciclos 2022-23 y 2024-25 con la misma
ventana SIMCE pre-pandemia deja de ser una simplificación del modelador y pasa a ser, al menos
para 2022-2023, la reproducción de lo que hizo el organismo. El test de congelamiento del
proyecto —correlación de 0,95 a 0,98 entre ciclos— lo había mostrado empíricamente sin conocer la
causa; ahora la causa tiene cita. Para 2024-2025 el mismo argumento se enuncia como **hecho
administrativo de la política pública**, no como cita metodológica, mientras no se disponga del
documento.

## 2. Ventana de medición del factor Superación, ciclo 2026-2027

Fuente: MINEDUC, *Documento Técnico SNED 2026-2027*, **p. 11, Cuadro 5**, ratificado en el
**Anexo 1, p. 18**.

> «Como en el caso de Efectividad, para el cálculo del factor Superación se considera las pruebas
> aplicadas en 2023, 2024, como se resume en el cuadro siguiente:»

| Indicador | Fuente | Período de referencia |
|---|---|---|
| Lenguaje y Matemática | SIMCE 4º Básico | **2023-2024** |
| Lenguaje y Matemática | SIMCE 6º Básico | **2018-2024** |
| Lenguaje y Matemática | SIMCE 2º Medio | **2023-2024** |

**8º Básico no aparece: queda fuera del ciclo.**

## 3. Exclusión del SIMCE 2022

Fuente: mismo documento, **p. 11** y nota **b** del Anexo 1, **p. 19**.

> «Cabe señalar que no se consideraron las diferencias de las pruebas SIMCE 2023 con respecto de
> las pruebas SIMCE 2022, dado que estas últimas fueron definidas como sin consecuencias para los
> establecimientos educacionales.»

> «b. La medición de este factor utiliza la estandarización de la diferencia de las pruebas SIMCE
> entre dos años consecutivos. En el SNED 2026-2027 no se consideró la diferencia de las pruebas
> SIMCE 2023-2022.»

## 4. Corrección por significancia

Fuente: MINEDUC, *Documento Técnico SNED 2026-2027*, **p. 12**; ratificado en *Documento Técnico
SNED 2022-2023*, **p. 18**.

> «Las diferencias corregidas por significancia corresponden a las diferencias reportadas
> estandarizadas, en los casos en que éstas sean significativas estadísticamente, y se consideran
> nulas en los casos en que el SIMCE reporta las diferencias como no significativas
> estadísticamente. El factor final considera el promedio de estas diferencias corregidas de cada
> nivel, de acuerdo con la información existente para cada establecimiento.»

Versión del ciclo 2022-2023, p. 18:

> «Las diferencias corregidas son iguales a las diferencias reportadas estandarizadas, en los
> casos en que éstas sean significativas estadísticamente, e iguales a 0 en los casos en que el
> SIMCE las reporte como no significativas estadísticamente.»

**Medido sobre el dato del proyecto:** 33.007 de 47.298 diferencias del bienio 2018-19 no son
estadísticamente significativas, un **69,8 %**, y por lo tanto valen cero según esta regla.

## 5. Promedio simple, sin ponderación por matrícula

Fuente: *Documento Técnico SNED 2026-2027*, **p. 12**.

> «El factor final considera el promedio de estas diferencias corregidas de cada nivel, de acuerdo
> con la información existente para cada establecimiento. Para el cálculo del Factor Superación se
> considera el promedio de las diferencias de cada nivel.»

Única excepción documentada, **p. 16**:

> «Así, en el caso que se hace necesario consolidar información, como por ejemplo los puntajes
> SIMCE del principal y sus anexos, se considera el promedio ponderado (por cantidad de alumnos)
> de los valores observados para cada establecimiento.»

## 6. Imputación por Grupo Homogéneo

Fuente: *Documento Técnico SNED 2026-2027*, **p. 12** y nota **d** del Anexo 1, **p. 18**.

> «Para los establecimientos que no cuentan con información para los Factores Efectividad y
> Superación se imputa el promedio del grupo homogéneo.»

> «d. En el caso de los establecimientos de Educación de Adultos (que no rinden la prueba SIMCE),
> de las Escuelas en contexto de encierro y de los establecimientos de Educación Parvularia, se
> les imputan valores para los factores Efectividad y Superación, que corresponden a los promedios
> del grupo homogéneo al cual pertenecen.»

**Aplica solo a Efectividad y Superación.** El sistema construido imputa por **mediana nacional**,
lo que constituye una divergencia metodológica declarada.

## 6.bis Cómo se calcula cada factor

Registrado el 2026-08-21. **Solo la primera fila tiene cita textual verificada**; el resto proviene
de una lectura asistida de los documentos técnicos y debe contrastarse contra la fuente antes de
citarse en la tesis. Se conserva porque cierra la pregunta P-6, que llevaba abierta desde el
inicio: cuatro de los seis factores no tenían fórmula documentada en el repositorio.

**Efectividad — 37 %.** Promedio simple de los puntajes SIMCE estandarizados de las pruebas
válidas rendidas. **Sin ponderación diferenciada por nivel ni por asignatura.**

> «El indicador se calcula como el promedio válido de los puntajes estandarizados de las pruebas
> rendidas por el establecimiento.» — *Documento Técnico SNED 2026-2027*, p. 11; ratificado en
> *Documento Técnico SNED 2022-2023*, p. 11

**Superación — 28 %.** Diferencia entre el bienio evaluado y el anterior, **estandarizada por la
Agencia de la Calidad**, no por el SNED. La población de referencia es el universo nacional de
establecimientos que rindieron las pruebas comparadas. Los documentos técnicos **no publican la
media ni la desviación** usadas: reciben la base ya estandarizada. Es lo que permite comparar en
una misma métrica la variación consecutiva de 4º básico con la de seis años de 6º básico.

**Iniciativa — 6 %.** Promedio simple de trece indicadores de la Ficha SNED, todos con igual peso:
actividades formativas complementarias, periodicidad del equipo de gestión, funcionamiento del
Consejo Escolar, apoyo a alumnos del PIE, compromisos de cobertura curricular, capacitación
docente y acciones de convivencia escolar.

**Integración y Participación — 5 %.** Promedio simple de siete indicadores: existencia y
operación del Consejo General de Profesores, Centro de Padres, Centro de Alumnos, incorporación de
la comunidad en compromisos, y la forma en que se informa a las familias los resultados SIMCE y
SNED.

**Mejoramiento de las Condiciones de Trabajo — 2 %.** Conteo de procesos administrativos
finalizados con sanciones graves de la Superintendencia de Educación en el período. **Se excluyen
del conteo las sanciones por discriminación y por PIE**, para no penalizar dos veces el mismo
hecho.

**Igualdad de Oportunidades — 22 %.** Tres subfactores con peso fijo:

| Subfactor | Peso dentro del factor | Contenido |
|---|---:|---|
| Rendimiento | 50 % | Promedio simple de tasa de aprobación y tasa de retención |
| Discriminación y sanciones indebidas | 40 % | Ausencia de expulsiones injustificadas, suspensión de matrícula por embarazo o repitencia |
| Integración | 10 % | Porcentaje de alumnos integrados, existencia legal del PIE, discapacidad múltiple o severa |

### La Ficha SNED

Cuestionario **de autorreporte**, completado por el director en la plataforma ministerial, y
**validado después por los Departamentos Provinciales de Educación**, que lo cotejan contra los
registros centrales de matrícula y convenio PIE. Las respuestas no se suman linealmente: se asigna
mayor puntaje a las alternativas que acreditan mecanismos reales de participación y mayor
frecuencia de ejecución.

**Qué ocurre si no se responde.** No existe regla de imputación. A diferencia de Efectividad y
Superación —donde el método inyecta el promedio del Grupo Homogéneo—, el establecimiento que no
responde la Ficha **obtiene cero de hecho** en Iniciativa, en Integración y en el subfactor de
integración de Igualdad. Se reporta que en el ciclo 2026-2027 no respondió el **12,9 %** de los
establecimientos elegibles, concentrados en Educación Especial. *Cifra sin cita verificada.*

## 6.ter Grupos Homogéneos: construcción y calendario

Fuente: *Documento Técnico SNED 2026-2027*, **pp. 6-7**.

> «La construcción de los Grupos Homogéneos en el SNED se efectúa al interior de cada región. La
> metodología para dicha construcción contempla tres etapas: [...] Etapa 2: Clasificación por nivel
> socioeconómico. Para formar los grupos homogéneos se utiliza una técnica estadística denominada
> "análisis de conglomerados", correspondiente específicamente al método de k-medias. Este método
> agrupa a los establecimientos minimizando la varianza dentro de los grupos y maximizando la
> varianza entre ellos. Se utilizan las siguientes variables, las cuales son previamente
> estandarizadas: IVE-SINAE (primera y segunda prioridad), Calificación Socioeconómica (CSE) y
> años de escolaridad de los padres (según el RSE).»

**Tres etapas, en orden:** zona urbana o rural → nivel de enseñanza, con grupo independiente para
educación especial → k-medias sobre las tres variables socioeconómicas. Todo **dentro de cada
región**, no a nivel nacional.

| Ciclo | Grupos conformados |
|---|---:|
| 2018-2019 | 126 |
| 2022-2023 | 136 |
| 2026-2027 | 138 |

### Calendario del ciclo, y por qué importa

| Momento | Qué ocurre |
|---|---|
| Septiembre año previo | Se consolidan RSH e IVE-SINAE y se corre k-medias |
| Octubre-noviembre | La clasificación se envía a encargados regionales del MINEDUC para verificación. En paralelo se aplica la Ficha SNED |
| Diciembre | Se incorporan ajustes territoriales y **los grupos quedan firmes** |
| Enero-febrero | Se calcula el índice y se ordena dentro de cada grupo ya congelado |
| Marzo | Publicación oficial de resultados y nómina de seleccionados |

### El Grupo Homogéneo no se comunica por anticipado

> «Los resultados de este análisis, con la clasificación inicial de los establecimientos por grupo
> homogéneo en cada región, son remitidos a los encargados regionales del Ministerio de Educación,
> para su verificación. Posteriormente, si corresponde, se incluyen los cambios propuestos por los
> encargados regionales a la clasificación inicial de grupos homogéneos.»

La comunicación ocurre **entre el nivel central y los encargados regionales**, no hacia los
establecimientos. El equipo directivo conoce su grupo **el mismo día en que se publican los
resultados**.

### Consecuencia, que no es la que parece a primera vista

Hay que separar dos cosas que se confunden con facilidad:

| Uso | ¿Es admisible usar `CLUSTER`? | Por qué |
|---|---|---|
| **Validación retrospectiva** del modelo | **Sí.** No hay fuga | El grupo queda firme en diciembre y el índice se calcula en enero-febrero. El predictor precede al resultado |
| **Simulación prospectiva** por un directivo | **No, no el del ciclo en curso** | Ese grupo no se le comunica hasta marzo, junto con los resultados. No lo tiene cuando querría simular |

Lo que un directivo **sí** conoce es el grupo del ciclo anterior. El propio repositorio midió su
estabilidad: alrededor del **81 %** de los establecimientos conserva el grupo entre ciclos
consecutivos, y un **18,6 %** cambia. Usar el grupo anterior como aproximación del vigente es
razonable y tiene su tasa de error medida, pero es una aproximación y debe declararse como tal en
el manual de usuario.

## 6.quater Selección de los establecimientos premiados

Fuente: *Documento Técnico SNED 2026-2027*, **p. 16**.

> «Con el objeto de efectuar la selección de los establecimientos, una vez ordenados de mayor a
> menor Índice SNED, se reconoce como establecimientos de mejor desempeño en cada grupo a aquellos
> que obtienen los mayores índices SNED y que representan en el agregado hasta el **25 % de la
> matrícula regional**. Un segundo grupo lo constituyen los establecimientos ubicados a
> continuación, hasta completar el **35 % de la matrícula regional**.»

**La selección no es por número de establecimientos: es por matrícula acumulada.** Se ordena por
índice dentro del grupo homogéneo y se van sumando matrículas hasta alcanzar el porcentaje
regional. Un colegio grande consume más cupo que uno pequeño con el mismo índice.

| Tramo | Cobertura | Beneficio |
|---|---|---|
| 1 | Hasta el 25 % de la matrícula regional | 100 % de la Subvención por Desempeño de Excelencia |
| 2 | Del 25 % al 35 % de la matrícula regional | 60 % de la subvención |

La unidad de competencia es el **Grupo Homogéneo dentro de cada región**. Un establecimiento de
Coquimbo nunca compite contra uno del Biobío, aunque compartan tipología socioeconómica.

### El algoritmo de adjudicación

*Descrito sin cita textual verificada. Contrastar contra la fuente antes de citarlo.* La
asignación se resuelve como un problema de optimización con restricciones, no como un corte plano
por puntaje:

1. Se parte sin establecimientos premiados.
2. Por región se arma una lista con el mejor índice de cada grupo homogéneo.
3. Se descartan los candidatos que incumplan tres restricciones:
   - índice inferior al promedio regional, excluido el grupo de educación especial;
   - índice inferior al máximo de los no premiados de un grupo del mismo tipo pero de menor nivel
     socioeconómico;
   - matrícula que, al sumarse, excede el límite regional del tramo.
4. Entre los candidatos válidos se premia a aquel cuya incorporación **minimiza la distancia
   cuadrada** entre la matrícula acumulada y la meta del tramo.
5. Se repite hasta agotar el cupo. El procedimiento corre dos veces: primero para el 25 %, después
   para el 35 %.

### Monto del beneficio

*Sin cita textual verificada.* Se paga por alumno, de modo que el monto depende de la matrícula.
Valores mensuales por estudiante declarados para el ciclo 2026-2027: **$7.463,89** de subvención
docente y **$522,65** de asistentes de la educación. Los establecimientos del tramo 2 perciben el
60 %.

La ley manda distribuir esos recursos: **90 %** entre todos los profesionales de la educación en
proporción a sus horas de contrato y **10 %** como incentivo a docentes destacados; el **100 %**
del fondo de asistentes se reparte entre ellos según jornada contratada.

## 6.quinquies La frontera de información: qué no se publica

Es la sección que sostiene la afirmación central de la tesis. Registrada el 2026-08-21, **sin cita
textual**: proviene de una lectura asistida y debe contrastarse contra la fuente antes de citarse.

**El único factor reconstruible con dato público es Efectividad**, que se alimenta de puntajes
SIMCE estandarizados. Los otros cinco dependen de insumos que no se publican desagregados.

| Factor | Ponderación | Insumo que no se publica |
|---|---:|---|
| Superación | 28 % | Reconstruible en parte: las diferencias y su significancia sí se publican |
| Igualdad de Oportunidades | 22 % | Respuestas de discriminación del cuestionario SIMCE de padres; variable de discapacidad múltiple o severa, que solo consta en la Ficha |
| Iniciativa | 6 % | Ficha SNED completa: indicadores IN-1 a INIC-13 |
| Integración y Participación | 5 % | Ficha SNED: indicadores INTE-1 a INTE-7 |
| Mejoramiento | 2 % | El subconjunto **ya filtrado** de sanciones graves, que excluye las ligadas a discriminación y PIE |
| **Total acotado** | **63 %** | |

**La aritmética confirma la cifra que el proyecto venía declarando.** 28 + 22 + 6 + 5 + 2 = **63 %**,
y 37 % de Efectividad es el complemento. El «63 % de la ponderación acotada por información no
publicada» que aparece en la documentación del sistema desde el inicio coincide exactamente con la
suma de los cinco factores no reconstruibles. La afirmación deja de ser una estimación y pasa a
tener una descomposición.

### Qué publica y qué no publica el Ministerio

**Publica:** el puntaje final de cada uno de los seis factores, normalizado de 0 a 100, y el índice
global, por establecimiento y por ciclo. Es exactamente lo que contienen los archivos `SNED_*.csv`
que el proyecto ingesta.

**No publica:**

- Las respuestas de la Ficha SNED, más de cuarenta preguntas de autorreporte validadas por los
  Departamentos Provinciales.
- Las respuestas desagregadas de discriminación del cuestionario de padres, protegidas por secreto
  estadístico.
- El subconjunto depurado de procesos sancionatorios que efectivamente entra al cálculo.
- El detalle aritmético por establecimiento: la ponderación de matrícula aplicada al fusionar
  sedes, el puntaje bruto antes de estandarizar, cuántos puntos restó cada sanción, y la posición
  dentro del grupo homogéneo antes de correr el algoritmo de adjudicación.

Se atribuye el procesamiento del índice al Centro de Economía Aplicada de la Universidad de Chile,
por encargo del MINEDUC. *Sin verificar.*

**Consecuencia para el alcance del sistema.** El simulador no puede reconstruir el índice oficial y
no lo pretende: estima. La opacidad no está solo en el algoritmo de adjudicación sino,
principalmente, en la inaccesibilidad de los microdatos de proceso. Esa distinción conviene tenerla
clara en la defensa, porque son dos cajas negras distintas y solo una es un problema de método.

## 7. Marco legal

Fuente: *Documento Técnico SNED 2026-2027*, **p. 4**.

> «(i) Marco Legal: La creación del instrumento está establecida en una ley (Ley 19.410, 1995,
> art. 15) y su metodología en un reglamento (Decreto 66 del Ministerio de Educación, 2006), que
> le otorgan un carácter de obligatoriedad y permanencia, garantizando además los recursos
> públicos para su financiamiento.»

### 7.1 Ley N° 19.410, artículo 15

**El texto de la ley no está disponible entre las fuentes consultadas**, de modo que no hay cita
textual del articulado. Lo que los documentos ministeriales le atribuyen: crea el Sistema Nacional
de Evaluación del Desempeño y **manda por ley que la medición considere seis factores**:
efectividad, superación, iniciativa, mejoramiento de las condiciones de trabajo, igualdad de
oportunidades, e integración y participación de profesores, padres y apoderados.

Que los seis factores estén fijados por ley es lo que impide alterarlos por vía administrativa, y
explica por qué las ponderaciones se mantuvieron estables incluso durante la pandemia.

### 7.2 Decreto N° 66 de 2006

Reglamento del SNED. Fija las ponderaciones de los seis factores, la normalización a escala 0-100,
la metodología de conformación de Grupos Homogéneos y el algoritmo de selección por tramos.
*Contenido sin cita textual verificada.*

Adaptaciones registradas, también sin cita: la incorporación de los liceos regidos por el Decreto
Ley N° 3.166 y la extensión del beneficio a los asistentes de la educación en el proceso 2008-2009;
y la adecuación de la Ficha SNED 2021 por el contexto de pandemia.

## 8. Ponderaciones vigentes

| Factor | Ponderación |
|---|---:|
| Efectividad | 37 % |
| Superación | 28 % |
| Igualdad de Oportunidades | 22 % |
| Iniciativa | 6 % |
| Integración y Participación | 5 % |
| Mejoramiento de las Condiciones de Trabajo | 2 % |

Ratificado además en el pie de página del *Esquema de registro Base SNED 2026-2027*, Centro de
Estudios, Unidad de Estadísticas.

---

## 9. Consecuencias para el sistema construido

Cada una de estas líneas es una diferencia entre lo que hace el software y lo que manda el método.
Ninguna es un error de programación: son decisiones tomadas sin la fuente a la vista, y ahora
tienen nombre.

| # | Lo que hace el sistema | Lo que manda el método | Estado |
|---|------------------------|------------------------|--------|
| C-1 | Calcula la variación como `actual − previo`, cruda | Diferencia **reportada, estandarizada y corregida por significancia** | Medido: la corrección lleva el R² del factor de 0,0316 a 0,2181 |
| C-2 | Imputa por mediana nacional | Promedio del **Grupo Homogéneo**, solo en Efectividad y Superación | Abierto |
| C-3 | Trata los cuatro niveles con la misma ventana | 4º básico y 2º medio: **2023-2024**. 6º básico: **2018-2024**. 8º básico: **fuera** | Abierto |
| C-4 | No usa `difgru_*` ni `siggru_*` | No son insumo del factor, pero son contexto publicado | Medido: aportan +0,0020, despreciable |
| C-5 | **Excluye** del entrenamiento los establecimientos con ficha no respondida | El método les asigna **cero de hecho** en Iniciativa, Integración y parte de Igualdad | Abierto: ver abajo |
| C-6 | La evaluación de acierto en la selección reparte **cupos por conteo** de establecimientos dentro del grupo | La regla real reparte **matrícula acumulada regional** hasta el 25 % y el 35 %, con tres restricciones y minimización de distancia cuadrada | Abierto: ver abajo |

**Sobre C-5.** El cuaderno de integración marca `ficha_no_respondida` cuando Iniciativa e
Integración valen cero simultáneamente, y excluye esos 168 casos del conjunto de entrenamiento con
el argumento de que son ruido administrativo. A la luz del método, esos ceros **no son ruido: son
la penalización real** que la política aplica a quien no responde. La exclusión sigue siendo
defendible —el modelo no debería aprender a predecir una omisión administrativa— pero deja de ser
una limpieza de datos y pasa a ser una **decisión de alcance**: el sistema no estima el índice de
un establecimiento que no respondió la Ficha. Corresponde declararlo así, y no como depuración.

**Sobre C-6.** Los guiones `evaluar_seleccion.py` y `validar_ciclo_2026_27.py` asignan a cada
grupo homogéneo tantos premiados como hubo realmente, y preguntan si el modelo habría elegido a
los mismos. Esa decisión se tomó **porque la regla oficial no estaba documentada**, y se declaró
como tal. Ahora que la regla está citada, la aproximación tiene un sesgo identificable: al repartir
por conteo y no por matrícula, favorece implícitamente a los establecimientos pequeños respecto de
lo que haría el algoritmo real. Emular la regla oficial —ordenar por índice estimado dentro del
grupo, acumular matrícula hasta el 25 % regional y aplicar las restricciones— convertiría la
evaluación de acierto en una réplica del procedimiento administrativo, no en una aproximación.

**C-3 es la que más importa y la más reciente.** El script de validación temporal alinea el ciclo
2026-27 con el bienio SIMCE 2023-24 completo, incluido 6º básico. Según el Cuadro 5, la variación
de 6º básico se mide contra **2018**, no contra 2023. La columna `dif_lect6b_rbd` publicada en el
archivo de 2024 compara contra la aplicación inmediatamente anterior, que no es 2018. Corresponde
verificar contra qué año compara efectivamente esa columna antes de usarla como insumo de
Superación.

## 10. Referencias en APA 7

Agencia de la Calidad de la Educación. (2024). *Bases de datos de resultados SIMCE por
establecimiento* [Conjunto de datos]. Ministerio de Educación. https://datosabiertos.mineduc.cl/

Biblioteca del Congreso Nacional de Chile. (1995). *Ley N° 19.410*. Ley Chile.

Ministerio de Educación. (2006). *Decreto N° 66: Reglamento del Sistema Nacional de Evaluación del
Desempeño de los Establecimientos Educacionales Subvencionados*.

Ministerio de Educación de Chile. (2018). *Sistema Nacional de Evaluación del Desempeño de los
Establecimientos Educacionales Subvencionados y de los Regidos por el Decreto Ley N° 3166 —
2018/2019*. División de Educación General.

Ministerio de Educación de Chile. (2022). *Sistema Nacional de Evaluación del Desempeño de los
Establecimientos Educacionales Subvencionados y de los Regidos por el Decreto Ley N° 3166 — SNED
2022/2023: Documento técnico*. División de Educación General.

Ministerio de Educación de Chile. (2025). *Sistema Nacional de Evaluación del Desempeño de los
Establecimientos Educacionales Subvencionados y de los Regidos por el Decreto Ley N° 3166 — SNED
2026/2027: Documento técnico*. División de Educación General.

Ministerio de Educación, Centro de Estudios. (2026). *Esquema de registro Base SNED 2026-2027*.
Unidad de Estadísticas.

## 11. Preguntas abiertas

Formuladas y **sin responder** a la fecha. Se registran para no volver a suponerlas.

| # | Pregunta | Por qué importa |
|---|----------|-----------------|
| ~~P-1~~ | ~~¿Conteo o matrícula acumulada?~~ | **Respondida: matrícula acumulada regional.** Cita textual, p. 16. Ver 6.quater y C-6 |
| ~~P-2~~ | ~~¿Nacional o regional?~~ | **Respondida: regional.** Los grupos se construyen dentro de cada región (pp. 6-7) |
| ~~P-3~~ | ~~¿Qué determina el tramo 25 % frente al 35 %?~~ | **Respondida:** 25 % paga el 100 % de la subvención; 25-35 % paga el 60 %. Hoy el sistema trata ambos como «premiado», lo que es una simplificación declarable |
| ~~P-4~~ | ~~¿Qué variables no se publican?~~ | **Respondida el 2026-08-21**, sección 6.quinquies. La suma de los cinco factores no reconstruibles da exactamente el 63 % declarado |
| ~~P-5~~ | ~~¿Cuándo quedan firmes los Grupos Homogéneos?~~ | **Respondida el 2026-08-21**, sección 6.ter. Firmes en diciembre; publicados en marzo |
| ~~P-6~~ | ~~¿Cómo se calculan Iniciativa, Integración, Mejoramiento e Igualdad?~~ | **Respondida el 2026-08-21**, sección 6.bis. Falta contrastar contra la fuente las partes sin cita |
| P-7 | ¿Contra qué año compara la columna `dif_*6b_rbd` publicada en el archivo SIMCE 2024? | Determina si sirve como insumo de Superación de 6º básico |

## 12. Historial de modificaciones

| Fecha | Sección | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-21 | — | Documento nuevo | Las citas metodológicas estaban dispersas en conversaciones y no en el repositorio |
| 2026-08-21 | 1 | Se declara la ausencia de los documentos técnicos 2020-2021 y 2024-2025 | Una consulta asistida reconstruyó sus tablas de fuentes sin respaldo; queda constancia de que esas ventanas son supuestos |
| 2026-08-21 | 9 | Se registra C-3: la ventana de 6º básico del ciclo 2026-2027 es 2018-2024 | Afecta al script de validación temporal, que asume el bienio completo |
| 2026-08-21 | 6.bis y 9 | Se documenta el cálculo de los seis factores y se abre C-5 sobre la ficha no respondida | Cierra P-6. Los ceros de la ficha no son ruido administrativo sino la penalización que aplica el método |
| 2026-08-21 | 1, 6.quinquies, 7 y 10 | Se incorpora el documento técnico 2018-2019, se descompone el 63 % de ponderación acotada, se declara que el texto de la Ley 19.410 no está disponible y se corrigen las referencias APA | Cierra P-4. El 63 % deja de ser una estimación: es la suma exacta de los cinco factores cuyos insumos no se publican |
| 2026-08-21 | 6.quater y 9 | Regla de selección por matrícula acumulada regional, sus tramos y el algoritmo de adjudicación. Se abre C-6 | Cierra P-1 y P-3. La evaluación de acierto del proyecto reparte por conteo, que ahora se sabe que es una aproximación con sesgo hacia los establecimientos pequeños |
| 2026-08-21 | 6.ter | Construcción y calendario de los Grupos Homogéneos | Cierra P-2 y P-5. Separa el uso retrospectivo del predictor, que es válido, del uso prospectivo por un directivo, que no dispone del grupo vigente |
