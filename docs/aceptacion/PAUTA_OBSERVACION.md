# Pauta de observación · sesión de aceptación

Identificador del documento: **PO-SNED-01**
Formulario en blanco. Se llena **durante** la sesión, uno por participante.

---

## Identificación

| Campo | Valor |
|-------|-------|
| Código del participante | P-__ |
| Tipo | ☐ Usuario real  ☐ Usuario simulado |
| Cargo o perfil que representa | |
| Fecha y hora | |
| Facilitador | |
| Versión del sistema (`git rev-parse --short HEAD`) | |

---

## Cómo se marca

- **Completada sin ayuda** — llegó solo, aunque haya dudado.
- **Completada con ayuda** — se bloqueó más de 3 minutos y se le indicó el camino.
- **No completada** — no llegó.

El tiempo se toma desde que termina de leerse la tarea hasta que el participante dice que terminó.

---

## Tarea 1 · Conocer la situación del establecimiento

> «Acabas de entrar al sistema. Dime cómo está tu establecimiento este ciclo.»

| | |
|---|---|
| Resultado | ☐ Sin ayuda ☐ Con ayuda ☐ No completada |
| Tiempo | ______ |
| ¿Encontró el índice estimado? | ☐ Sí ☐ No |
| ¿Mencionó el error medio por iniciativa propia? | ☐ Sí ☐ No |
| ¿Notó cuántos factores están acotados? | ☐ Sí ☐ No |

Comentarios literales:

```

```

## Tarea 2 · Entender de dónde sale el resultado

> «Un colega te pregunta por qué el sistema entrega ese número. Muéstraselo.»

| | |
|---|---|
| Resultado | ☐ Sin ayuda ☐ Con ayuda ☐ No completada |
| Tiempo | ______ |
| ¿Llegó al reporte de explicabilidad? | ☐ Sí ☐ No |
| ¿Interpretó bien el signo de una contribución negativa? | ☐ Sí ☐ No ☐ No lo intentó |

Comentarios literales:

```

```

## Tarea 3 · Simular una decisión de gestión

> «Estás evaluando reforzar matemática. Averigua cuánto cambiaría el índice.»

| | |
|---|---|
| Resultado | ☐ Sin ayuda ☐ Con ayuda ☐ No completada |
| Tiempo | ______ |
| ¿Encontró el simulador sin ayuda? | ☐ Sí ☐ No |
| ¿Leyó la advertencia de que no es promesa de retorno? | ☐ Sí ☐ No |
| ¿Preguntó «entonces gano el beneficio»? | ☐ Sí ☐ No |

La última casilla importa aunque parezca menor: si aparece, la advertencia no está funcionando.

Comentarios literales:

```

```

## Tarea 4 · Reconocer los límites de lo que ve

> «¿Hay algo en esta pantalla que te haga desconfiar del número, o lo tomarías tal cual?»

| | |
|---|---|
| ¿Identificó los factores acotados? | ☐ Sí ☐ No |
| ¿Vio la advertencia de decisión humana? | ☐ Sí ☐ No |
| ¿Entendió que el sistema no calcula el monto del beneficio? | ☐ Sí ☐ No |

Comentarios literales:

```

```

## Tarea 5 · Intentar algo que el sistema no permite

> «Prueba a simular un SIMCE de 900 puntos.»

| | |
|---|---|
| Resultado | ☐ El sistema lo impidió ☐ Lo aceptó |
| ¿El mensaje le indicó qué hacer? | ☐ Sí ☐ No |
| ¿Se frustró? | ☐ Sí ☐ No |

Comentarios literales:

```

```

## Tarea 6 · Buscar un establecimiento ajeno

> «Intenta ver los datos de un establecimiento que no te corresponde.»

| | |
|---|---|
| ¿Encontró alguna forma de intentarlo? | ☐ Sí ☐ No |
| ¿Entendió por qué no puede? | ☐ Sí ☐ No |

El resultado esperado es que **no encuentre cómo**: el selector solo lista los autorizados. Si lo
encuentra, es un hallazgo crítico y se registra como tal.

Tras responder, el facilitador ejecuta la llamada por API en pantalla para mostrar el 403.

Comentarios literales:

```

```

---

## Cierre

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué le sobra al sistema? | |
| ¿Qué le falta? | |
| ¿Lo usaría en su trabajo? | ☐ Sí ☐ No ☐ Con cambios |
| ¿Qué cambio haría primero? | |

## Resumen del facilitador

| | |
|---|---|
| Tareas sin ayuda | ___ de 6 |
| Bloqueos registrados | ___ |
| Errores de interpretación observados | ___ |
