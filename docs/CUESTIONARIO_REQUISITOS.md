# Cuestionario de profundización de requisitos
### Rediseño OOP del backend · Modelo de clases · Estrategia de pruebas

Documento de trabajo. Cada pregunta viene con **por qué importa** y **mi recomendación
como arquitecto**, para que puedas responder rápido o discrepar con fundamento.

Responde solo lo que tengas claro; lo que dejes en blanco lo resuelvo con la recomendación
por defecto y te lo marco como supuesto en el entregable.

---

## Punto de partida: qué es OOP y qué es funcional hoy en tu backend

Antes de decidir, conviene ver el estado real. No partes de cero:

| Módulo | Paradigma actual | Comentario |
|--------|------------------|------------|
| `q2_modelamiento/contrato.py` | **OOP puro** | `EstrategiaPredictiva` (ABC) + dataclasses inmutables. Ya es tu núcleo de clases. |
| `q2_modelamiento/estrategias/` | **OOP** | Dos clases concretas que heredan del contrato. |
| `q2_modelamiento/catalogo.py` | Mixto | `Factor` es dataclass, pero `reconstruir_indice()` es función suelta. |
| `q2_modelamiento/registro_modelos.py` | **Funcional** | Funciones con `lru_cache`. Candidato natural a `RegistroDeModelos`. |
| `q1_ingesta/calidad.py` | **Funcional** | `ReporteCalidad` es dataclass, pero `aplicar_cuarentena()` es función. |
| `q1_ingesta/fuentes.py` | Datos + funciones | `Fuente` es dataclass; falta el comportamiento (`leer()`, `validar()`). |
| `q3_servicio/servicios/motor.py` | **Funcional** | Fachada de funciones. Candidato a `ServicioDePrediccion`. |
| `q3_servicio/api/v1/routers/` | Funcional (idiomático) | FastAPI es funcional por diseño; forzar clases aquí es ir contra el framework. |

**El trabajo real de migración está en Q1 y en la capa de servicios de Q3.** Q2 ya es orientado
a objetos y es donde vive el grueso de tu modelo de clases.

---

## A. Alcance y estilo del rediseño orientado a objetos

**A1. ¿Hasta dónde llega el rediseño OOP?**
Opciones: (a) todo el backend incluidos los routers; (b) dominio + servicios en clases, routers
funcionales; (c) solo el cuanto 1, porque Q2 ya lo está.
*Por qué importa:* forzar clases en los routers de FastAPI produce código peor y contradice al
framework — los evaluadores de arquitectura lo notan.
*Recomendación:* (b). Los routers son adaptadores delgados de 5 líneas; el modelo de clases se
defiende con el dominio, no con el transporte.

**A2. ¿Qué estilo arquitectónico de clases adoptas?**
Opciones: (a) DDD táctico (Entidad, Objeto de Valor, Agregado, Repositorio, Servicio de Dominio);
(b) Arquitectura Hexagonal / Puertos y Adaptadores; (c) capas clásicas Modelo–Servicio–DAO.
*Por qué importa:* determina los estereotipos del diagrama de clases y el vocabulario de la defensa.
*Recomendación:* (b) Hexagonal. Encaja de forma natural con lo que ya tienes: `EstrategiaPredictiva`
**ya es un puerto**, y las dos estrategias **ya son adaptadores**. Puedes argumentar continuidad
en vez de rehacer.

**A3. ¿Prefieres herencia o composición donde ambas sirvan?**
*Por qué importa:* la tesis cita explícitamente "favorecer la composición sobre la herencia"
(Freeman et al.). Conviene que el diagrama lo demuestre, no solo que el texto lo afirme.
*Recomendación:* composición, con herencia reservada a los contratos abstractos.

**A4. ¿Quieres inyección de dependencias explícita?**
Es decir, `ServicioDePrediccion(estrategia, repositorio)` en vez de que el servicio construya
sus propias dependencias.
*Por qué importa:* es lo que hace testeables las clases sin tocar disco ni cargar modelos de 60 MB.
*Recomendación:* sí, por constructor. Habilita dobles de prueba y es una relación visible en UML.

**A5. ¿Uso de patrones de diseño adicionales a Strategy?**
Candidatos concretos en tu dominio: **Repository** (acceso a establecimientos), **Factory**
(construcción de estrategias, ya existe como función), **Template Method** (el flujo de ingesta
es idéntico por fuente y solo cambia el parser), **Observer** (alertas), **Specification**
(reglas de cuarentena componibles), **Decorator** (cachear o auditar predicciones).
*Por qué importa:* cada patrón que uses debe justificarse por una fuerza real, no por vistosidad.
*Recomendación:* Repository, Factory y Template Method. Los otros tres son sobreingeniería aquí.

**A6. ¿Las clases de dominio deben ser inmutables?**
*Recomendación:* sí para objetos de valor (`Prediccion`, `ExplicacionLocal`, `Factor`);
mutables solo donde haya ciclo de vida real (`ReporteCalidad` acumula durante la ingesta).

**A7. ¿Quieres que las reglas de negocio vivan en las entidades o en servicios de dominio?**
Ejemplo: ¿`Establecimiento.esta_en_riesgo()` o `EvaluadorDeRiesgo.evaluar(establecimiento)`?
*Recomendación:* modelo rico. Que `Establecimiento` y `ResultadoIndice` tengan comportamiento;
un modelo anémico (puros getters) es la crítica más frecuente en defensas de tesis.

**A8. ¿Cuántas clases esperas en el diagrama final?**
*Por qué importa:* un diagrama de 60 clases es ilegible en una defensa; uno de 8 parece pobre.
*Recomendación:* 18–25 clases de dominio en el diagrama principal, más diagramas de detalle
por paquete si la rúbrica los pide.

---

## B. Modelo de clases y diagramas

**B1. ¿Qué diagramas UML necesitas exactamente?**
Candidatos: clases, secuencia, componentes, despliegue, estados, casos de uso, actividad.
*Por qué importa:* cada uno cuesta y no todos aportan aquí. El de estados casi no aplica a tu dominio.
*Recomendación:* clases (obligatorio), secuencia (2–3 flujos clave), componentes (los cuatro cuantos).

**B2. ¿En qué formato los quieres?**
Opciones: (a) PlantUML o Mermaid versionado en `docs/diagramas/` — texto, diffeable, regenerable;
(b) herramienta gráfica externa (StarUML, Draw.io, Enterprise Architect) — mejor para exportar a Word.
*Recomendación:* PlantUML en el repo **y** exportación PNG/SVG para la tesis. Lo mejor de ambos.

**B3. ¿El diagrama documenta el código que existirá, o el código se deriva del diagrama?**
*Por qué importa:* define el orden de trabajo y quién manda si divergen.
*Recomendación:* diagrama primero, código después, y una prueba que verifique que no divergen.

**B4. ¿Debe el diagrama de clases reflejar también el modelo de datos de PostgreSQL?**
*Por qué importa:* hay un desajuste objeto-relacional real: tus 4 esquemas ya están normalizados
en formato largo y las clases de dominio no los espejan uno a uno.
*Recomendación:* separarlos. Diagrama de clases (dominio) y modelo entidad-relación (persistencia)
son artefactos distintos; unirlos produce el clásico modelo anémico acoplado a tablas.

**B5. ¿Qué flujos quieres en los diagramas de secuencia?**
Candidatos: predicción completa (login → RBAC → carga → predicción → respuesta), simulación ICE,
generación de explicación Shapley, ingesta con cuarentena, verificación bianual de deriva.
*Recomendación:* los tres primeros — son los que la interfaz expone al usuario.

**B6. ¿Necesitas trazabilidad explícita entre clases y objetivos específicos?**
Es decir, una tabla que diga qué clase implementa qué OE.
*Recomendación:* sí. Es barato de producir y suele ser criterio de rúbrica.

---

## C. Estructura de la carpeta de pruebas

**C1. ¿Cómo organizas los cuatro tipos de prueba?**
Opciones: (a) por tipo — `tests/unitarias/`, `tests/integracion/`, `tests/aceptacion/`,
`tests/compatibilidad/`; (b) por cuanto — `tests/q1/`, `tests/q2/`…, con marcadores por tipo;
(c) híbrido: por tipo en el primer nivel, por cuanto adentro.
*Por qué importa:* hoy tienes 18 pruebas con marcadores (`datos`, `modelo`, `api`) en una sola carpeta.
*Recomendación:* (c). Refleja la nomenclatura que la tesis exige y conserva la trazabilidad al cuanto.

**C2. ¿Migro las 18 pruebas actuales o las conservo en paralelo?**
*Recomendación:* migrar. `test_qa_datos` → unitarias/integración de Q1; `test_qa_modelo` → unitarias
de Q2; `test_qa_api` → integración y aceptación de Q3; `test_arquitectura` → una categoría propia.

**C3. ¿Qué cobertura de código exiges como compuerta?**
*Por qué importa:* un umbral que nadie alcanza se termina desactivando, y entonces no existe.
*Recomendación:* 80 % en dominio (Q1, Q2), 60 % global, 0 % exigido en notebooks.

**C4. ¿Las pruebas pueden cargar los modelos `.joblib` reales?**
*Por qué importa:* son 220 MB y tardan; si las pruebas dependen de ellos, nadie las corre y no
funcionan en un entorno limpio donde los artefactos están git-ignorados.
*Recomendación:* unitarias con dobles de prueba; un único test de integración marcado como `lento`
que sí cargue el artefacto real y se excluya por defecto.

**C5. ¿Necesitas datos de prueba sintéticos versionados?**
Un `tests/fixtures/` con 50 establecimientos ficticios en parquet, que sí entre a git.
*Recomendación:* sí. Es la única forma de que las pruebas corran en una máquina recién clonada.

**C6. ¿Quieres pruebas de propiedades además de las de ejemplo?**
Ejemplo: "para cualquier combinación válida de factores, el índice reconstruido está en [0, 100]".
*Recomendación:* opcional, pero dos o tres con Hypothesis dan mucho valor argumental en la defensa.

**C7. ¿Las pruebas de arquitectura crecen?**
Hoy verificas fronteras entre cuantos. Podrías añadir: que toda clase de dominio sea inmutable,
que ningún router tenga más de N líneas, que toda estrategia implemente el contrato completo.
*Recomendación:* sí, tres o cuatro reglas más. Son el argumento más fuerte de que la arquitectura
no es solo un dibujo.

---

## D. Plan de pruebas de integración

**D1. ¿Qué integraciones cubres?**
Candidatos: Q1→Q2 (parquet alimenta al motor), Q2→Q3 (Strategy tras HTTP), Q3→PostgreSQL,
Q3→Q4 (contrato JSON), Q1→fuentes MINEDUC reales.
*Recomendación:* las cuatro primeras. La quinta no es testeable de forma determinista.

**D2. ¿PostgreSQL real o en memoria?**
*Por qué importa:* SQLite no soporta esquemas, vistas materializadas ni `PERCENT_RANK` como los usas.
*Recomendación:* PostgreSQL real vía `docker compose`, con marcador `requiere_bd` para poder omitirlas.

**D3. ¿Quién es responsable del contrato Q3↔Q4?**
Opciones: pruebas de contrato con esquema OpenAPI, pruebas de contrato dirigidas por consumidor
(estilo Pact), o simple verificación de tipos TypeScript.
*Recomendación:* validar las respuestas contra el esquema OpenAPI generado. Pact es desproporcionado
para un consumidor único.

**D4. ¿Qué haces con la latencia de SHAP en las pruebas?**
*Por qué importa:* calcular Shapley exacto en un test lo vuelve lento y frágil.
*Recomendación:* fijar un presupuesto explícito (ej. < 2 s por explicación) y probarlo una sola vez,
marcado como `lento`.

**D5. ¿Pruebas de integración de la ingesta con archivos reales del MINEDUC?**
*Recomendación:* con una muestra recortada versionada en `tests/fixtures/`, no con los 250 MB.

**D6. ¿Ejecutas las pruebas de integración en cada Sprint Review o bajo demanda?**
*Recomendación:* en cada Sprint Review, como parte de la compuerta 2 de la Definición de Terminado.

---

## E. Plan de pruebas de aceptación

**E1. ¿Quién es el criterio de aceptación: el profesor guía, un directivo real, o ambos?**
*Por qué importa:* la tesis excluye explícitamente los estudios de satisfacción de usuarios, así que
la aceptación debe formularse como **verificación funcional**, no como medición de usabilidad.
*Recomendación:* profesor guía como validador, criterios redactados como funcionalidad verificable.

**E2. ¿Formato de los criterios: Gherkin (Dado/Cuando/Entonces) o lista de verificación?**
*Recomendación:* Gherkin. Se lee igual de bien en la tesis que en el código, y `pytest-bdd`
lo ejecuta directamente. Cada historia de usuario del Product Backlog se convierte en escenarios.

**E3. ¿Qué historias de usuario deben tener prueba de aceptación?**
Tu meta declarada es ≥ 90 % de cobertura funcional sobre los casos de uso del Product Backlog.
*Pregunta concreta:* ¿cuántas historias tiene hoy tu Product Backlog? Lo necesito para dimensionar.

**E4. ¿La aceptación se ejecuta contra la API, contra la interfaz, o ambas?**
*Recomendación:* contra la API para la lógica de negocio; contra la interfaz solo para los tres
flujos de las ventanas. Automatizar toda la interfaz es caro y frágil.

**E5. ¿Qué escenarios negativos son obligatorios?**
Candidatos: RBAC bloquea RBD ajeno, RBD inexistente, artefacto ausente, factor inválido,
variable no simulable, sesión expirada.
*Recomendación:* los seis. Los escenarios negativos son donde se cae la mayoría de las defensas.

**E6. ¿Se prueba explícitamente el principio "la IA asiste, el directivo decide"?**
Ejemplo de escenario: "toda respuesta de predicción incluye la advertencia de decisión humana".
*Recomendación:* sí. Convierte tu premisa ética en un requisito verificable, no en una declaración.

**E7. ¿Necesitas evidencia documental (capturas, actas) además del resultado automatizado?**
*Recomendación:* sí, un reporte HTML de pytest archivado por Sprint sirve de acta.

---

## F. Plan de compatibilidad de navegadores

**F1. ¿Qué navegadores y versiones entran en la matriz?**
*Por qué importa:* sin criterio, la matriz crece sin fin.
*Recomendación:* Chrome, Edge y Firefox en sus dos últimas versiones, más Safari si algún sostenedor
usa Mac. Justifica la elección con la cuota de mercado del segmento educacional chileno.

**F2. ¿Entra móvil o es solo escritorio?**
*Por qué importa:* tu público son sostenedores y directivos, que trabajan en escritorio; pero un
dashboard que se rompe en tablet se nota en una demostración.
*Recomendación:* escritorio como objetivo y tablet como "degradación aceptable" declarada.

**F3. ¿Resoluciones objetivo?**
*Recomendación:* 1366×768 (el portátil institucional típico) y 1920×1080. Declarar 1280 como mínimo.

**F4. ¿Automatizada o manual?**
Opciones: (a) Playwright con los tres motores — automatizable y reproducible; (b) matriz manual
documentada con capturas; (c) híbrido: humo automatizado en los tres motores, resto manual.
*Recomendación:* (c). Playwright instala los tres navegadores con un comando y no cuesta licencia.

**F5. ¿Qué se verifica exactamente en cada navegador?**
Candidatos: renderizado de los gráficos Recharts (SVG), interacción del control del simulador,
formato de números y decimales (coma vs punto en español de Chile), fechas, descarga de reportes.
*Recomendación:* los tres primeros son los que realmente se rompen entre motores.

**F6. ¿Accesibilidad entra en el alcance?**
Contraste, navegación por teclado, lectores de pantalla.
*Por qué importa:* es fácil de justificar como fuera de alcance, pero hay que declararlo.
*Recomendación:* contraste y navegación por teclado sí (baratos); lectores de pantalla, fuera
de alcance declarado.

**F7. ¿Rendimiento entra aquí o es un plan aparte?**
*Recomendación:* un umbral simple en el plan de compatibilidad (primera pintura < 3 s en el
navegador más lento de la matriz). Un plan de carga completo es desproporcionado para un prototipo.

---

## G. Trazabilidad con la tesis

**G1. ¿Estos planes son documentos separados o secciones del Capítulo 3?**
*Recomendación:* documentos vivos en `docs/pruebas/` y una síntesis en la tesis. Así el repositorio
es la fuente de verdad y la tesis cita.

**G2. ¿Los planes deben seguir alguna plantilla o norma?**
Candidatos: IEEE 829, ISO/IEC 29119, o formato libre de la carrera.
*Pregunta concreta:* ¿la rúbrica exige alguna? Si hay una plantilla obligatoria, la sigo al pie.

**G3. ¿Idioma y convención de nombres?**
Hoy el código está en español (`predecir`, `explicar`, `EstrategiaPredictiva`).
*Recomendación:* mantener español. La coherencia con el dominio pesa más que la convención anglosajona,
y facilita la lectura del diagrama en la defensa.

**G4. ¿Qué entra en la próxima entrega y qué puede esperar?**
*Pregunta concreta:* ¿tienes fecha de hito? Con eso priorizo entre el rediseño OOP y los planes
de prueba, que compiten por el mismo tiempo.

---

## Lo que yo haría, si tuviera que decidir solo

1. **Hexagonal sobre lo que ya existe.** `EstrategiaPredictiva` es un puerto; formalizo los otros
   tres (repositorio de establecimientos, registro de modelos, lector de fuentes) y el diagrama
   sale coherente sin rehacer Q2.
2. **Routers funcionales, dominio OOP.** Defender clases donde aportan, y no pelear con FastAPI.
3. **`tests/` híbrido** — por tipo arriba, por cuanto adentro — y migro las 18 pruebas actuales.
4. **Gherkin para aceptación**, ejecutable con `pytest-bdd`: el mismo texto sirve en la tesis y en CI.
5. **Playwright para el humo en tres motores** y matriz manual documentada para el resto.
6. **PlantUML versionado** más exportación PNG, con una prueba que verifique que el diagrama
   y el código no divergen.
