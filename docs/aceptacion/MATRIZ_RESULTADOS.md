# Matriz de resultados de las pruebas de aceptación

Identificador del documento: **MR-SNED-01**
Estado: **en blanco, a la espera de la sesión.**

Se llena después de cada sesión. Es el documento que la rúbrica del Hito 3 pide como «matriz de
resultados de las pruebas de aceptación y las correcciones derivadas del testeo».

---

## 1. Datos de la ejecución

| Campo | Valor |
|-------|-------|
| Fecha de la sesión | |
| Participantes | n = ___ |
| Tipo | ☐ Usuario real ☐ Usuario simulado |
| Versión del sistema | |
| Facilitador | |

## 2. Escenarios de `PLAN_ACEPTACION.md`

Los once escenarios redactados. **Obl.** marca los que su fallo bloquea la aceptación sin importar
la cobertura alcanzada.

| ID | Escenario | Tipo | Obl. | Vía | Resultado | Evidencia |
|----|-----------|------|:----:|-----|-----------|-----------|
| A-01 | Consultar el índice estimado | Positivo | | Usuario · Tarea 1 | ☐ Aprueba ☐ Falla | |
| A-02 | Entender por qué se obtuvo ese resultado | Positivo | | Usuario · Tarea 2 | ☐ Aprueba ☐ Falla | |
| A-03 | Simular el efecto de mover una variable | Positivo | | Usuario · Tarea 3 | ☐ Aprueba ☐ Falla | |
| A-04 | El control de acceso bloquea un RBD ajeno | Negativo | ✔ | API, ante el participante | ☐ Aprueba ☐ Falla | |
| A-05 | RBD inexistente responde 404 | Negativo | ✔ | API | ☐ Aprueba ☐ Falla | |
| A-06 | Artefacto ausente responde 503 | Negativo | ✔ | API | ☐ Aprueba ☐ Falla | |
| A-07 | Variable no simulable responde 422 | Negativo | ✔ | API | ☐ Aprueba ☐ Falla | |
| A-08 | Valor fuera de rango responde 422 | Negativo | ✔ | Usuario · Tarea 5 | ☐ Aprueba ☐ Falla | |
| A-09 | Sesión expirada responde 401 | Negativo | ✔ | API | ☐ Aprueba ☐ Falla | |
| A-10 | La IA asiste, el directivo decide | Ético | ✔ | Usuario · Tarea 4 + C6 | ☐ Aprueba ☐ Falla | |
| A-11 | La frontera de información es visible | Ético | ✔ | Usuario · Tarea 4 + C3 | ☐ Aprueba ☐ Falla | |

| Resumen | Valor |
|---------|-------|
| Escenarios aprobados | ___ de 11 |
| Obligatorios aprobados | ___ de 8 |
| **¿Aceptación aprobada?** | ☐ Sí ☐ No |

## 3. Resultados por instrumento

| Métrica | Umbral | Obtenido | ¿Cumple? |
|---------|--------|----------|----------|
| Tareas completadas sin ayuda | ≥ 5 de 6 | | |
| Comprensión (sección 2) | ≥ 4 de 6 | | |
| Puntaje de usabilidad | ≥ 68 | | |
| Errores de interpretación | Se reportan todos | | |

**El umbral no se mueve para que un resultado apruebe.** Si no se alcanza, se declara.

## 4. Hallazgos

Uno por fila. La severidad se asigna con el mismo criterio de `PLAN_CALIDAD.md` §9.

| ID | Descripción del hallazgo | Dónde | Severidad | Decisión | Commit |
|----|--------------------------|-------|-----------|----------|--------|
| H-01 | | | ☐ Crítica ☐ Alta ☐ Media ☐ Baja | ☐ Corregido ☐ Declarado abierto ☐ Descartado | |
| H-02 | | | | | |
| H-03 | | | | | |

Criterio de severidad para esta prueba:

| Severidad | Qué la constituye aquí |
|-----------|------------------------|
| **Crítica** | El participante alcanzó un establecimiento fuera de su jurisdicción, o concluyó que el sistema le garantiza el beneficio |
| **Alta** | Interpretó la estimación como cifra oficial, o no reconoció la incertidumbre |
| **Media** | No completó una tarea sin ayuda |
| **Baja** | Molestia de interfaz sin consecuencia sobre la interpretación |

## 5. Correcciones derivadas

| Hallazgo | Corrección aplicada | Archivo | Verificada por |
|----------|--------------------|---------|----------------|
| | | | |

**Los hallazgos que no se corrijan antes de la entrega quedan aquí como abiertos, con su motivo.**
No se borran. Un hallazgo silenciado es peor que uno sin resolver.

## 6. Conclusión de la sesión

```

```

## 7. Historial de modificaciones

| Fecha | Sección | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-15 | — | Documento nuevo, en blanco | La rúbrica del Hito 3 exige matriz de resultados; no existía |
