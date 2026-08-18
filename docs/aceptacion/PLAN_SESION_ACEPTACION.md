# Plan de la sesión de aceptación con usuario

Identificador del documento: **PSA-SNED-01**
Fecha: **15 de agosto de 2026**
Complementa: `docs/planes/PLAN_ACEPTACION.md` (PPA-SNED-01), que redacta los once escenarios.

Aquel plan dice **qué** debe aceptarse. Este dice **cómo** se conduce la sesión, **quién**
participa, **qué se registra** y **con qué instrumentos**. Los formularios en blanco están en esta
misma carpeta.

---

## 1. Objetivo de la sesión

Comprobar que una persona del perfil destinatario —equipo directivo o sostenedor— puede completar
las tareas del sistema sin ayuda, y que **interpreta correctamente lo que ve**.

La segunda parte es la que importa en este proyecto. Un simulador que se usa bien pero se entiende
mal es peor que uno que no se usa: el índice tiene consecuencia monetaria, y una lectura equivocada
de una estimación orienta mal una decisión de gestión.

## 2. Participantes y honestidad sobre el perfil

| Rol | Quién | Qué hace |
|-----|-------|----------|
| Participante | Persona del perfil destinatario | Ejecuta las tareas pensando en voz alta |
| Facilitador | El tesista | Lee las tareas, **no ayuda**, registra tiempos y bloqueos |
| Observador | Opcional | Toma notas literales |

**Declaración obligatoria en el informe.** El tipo de participante cambia el valor de la evidencia
y no se puede difuminar:

| Tipo | Qué es | Cómo se declara |
|------|--------|-----------------|
| **Usuario real** | Directivo o sostenedor en ejercicio | «Prueba de aceptación con usuario real, n = X» |
| **Usuario simulado** | Alguien que representa el perfil sin ejercerlo: un par, el profesor guía, un docente | «Prueba de aceptación **simulada**, con participante que representa el perfil» |
| **Autoevaluación** | El propio tesista ejecuta los escenarios | No es prueba de aceptación. Se reporta como verificación funcional |

La rúbrica del hito admite usuario real o simulado. Lo que no admite ninguna rúbrica es presentar
una cosa como la otra.

## 3. Preparación previa

1. Sistema levantado y verificado antes de que llegue el participante. Si algo falla durante la
   sesión, se registra como hallazgo y no se arregla en caliente.
2. Cuenta de demostración con jurisdicción sobre al menos dos establecimientos.
3. Los tres formularios impresos o abiertos: pauta de observación, cuestionario y acta.
4. Datos del participante anonimizados desde el inicio: **P-01**, **P-02**. Ningún nombre en los
   documentos que van a la tesis.

## 4. Estructura de la sesión — 60 minutos

| Bloque | Minutos | Qué ocurre |
|--------|---------|------------|
| Encuadre | 5 | Qué es el sistema, qué se le pide, que **no se le evalúa a él sino al software** |
| Consentimiento | 3 | Se explica qué se registra y se firma el acta en su sección 1 |
| Tareas guiadas | 30 | Las seis tareas de la pauta de observación, en orden |
| Preguntas de comprensión | 10 | Sección 2 del cuestionario. Es la parte crítica |
| Cuestionario de usabilidad | 7 | Los diez ítems de la escala |
| Cierre abierto | 5 | Qué le sobra, qué le falta, si lo usaría |

## 5. Regla del facilitador

**No se ayuda, no se sugiere, no se corrige.** Ante una pregunta del participante, la única
respuesta admitida es «¿qué harías tú?».

Si se bloquea más de **tres minutos** en una tarea, se marca como no completada, se le indica el
camino y se continúa. Un bloqueo es un hallazgo, no un fracaso de la sesión.

Se registran los comentarios **literales**, no interpretados. «No sé si este número es bueno o
malo» es un dato; «el usuario no comprendió la escala» es una conclusión, y la conclusión va
después.

## 6. Qué escenarios puede ejecutar una persona y cuáles no

De los once escenarios de `PLAN_ACEPTACION.md`, no todos son alcanzables desde la interfaz:

| Escenario | ¿Lo puede provocar el participante? | Cómo se verifica |
|-----------|-------------------------------------|------------------|
| Consultar el índice estimado | Sí | Tarea 1 |
| Entender por qué se obtuvo | Sí | Tarea 2 |
| Simular el efecto de una variable | Sí | Tarea 3 |
| Los cinco factores acotados están marcados | Sí | Tarea 4 y pregunta de comprensión |
| La advertencia de decisión humana está presente | Sí | Tarea 4 |
| RBD ajeno bloqueado (403) | **No.** El selector solo lista los autorizados | Inducido por API, ante el participante |
| RBD inexistente (404) | No | ídem |
| Artefacto ausente (503) | No | ídem |
| Variable no simulable (422) | No | ídem |
| Valor fuera de rango (422) | Parcial, según el control de la interfaz | Tarea 5 |
| Sesión expirada (401) | No | ídem |

**Que seis escenarios no sean alcanzables desde la interfaz es un resultado, no una carencia.** Es
la consecuencia directa de la decisión de diseño de no poner un campo libre de RBD. Se demuestra
ante el participante ejecutando la llamada por API en pantalla, y se registra así en el acta.

## 7. Qué se mide

| Dimensión | Instrumento | Umbral declarado |
|-----------|-------------|------------------|
| Completitud de tareas | Pauta de observación | ≥ 5 de 6 sin ayuda |
| Tiempo por tarea | Pauta de observación | Sin umbral: se reporta |
| Comprensión de lo mostrado | Cuestionario §2 | ≥ 4 de 6 respuestas correctas |
| Usabilidad percibida | Cuestionario §3 | ≥ 68 puntos, valor de referencia de la escala |
| Errores de interpretación | Registro literal | Cada uno se documenta, ninguno se descarta |

**Advertencia estadística que debe ir en el informe.** Con uno o dos participantes, el puntaje de
usabilidad **no es una medición**: es un indicador de un caso. Se reporta el valor crudo y se
declara el número de participantes junto a él, siempre. Un puntaje sin su n es una cifra que
engaña.

## 8. Después de la sesión

1. Transcribir la pauta el mismo día, mientras el recuerdo está fresco.
2. Volcar cada hallazgo a `MATRIZ_RESULTADOS.md` con severidad y decisión.
3. Firmar el acta.
4. Los hallazgos que se corrijan antes de la entrega se marcan como corregidos **con el commit que
   los corrige**. Los que no, quedan declarados como abiertos. No se borran.

## 9. Historial de modificaciones

| Fecha | Sección | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-15 | — | Documento nuevo | `PLAN_ACEPTACION.md` redactaba los escenarios pero no existía protocolo de sesión ni instrumentos |
