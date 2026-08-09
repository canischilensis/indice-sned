# Plan de pruebas de compatibilidad de navegadores

**Identificador:** PPC-SNED-01 · **Versión:** 1.0 · **Sistema:** Interfaz del ecosistema SNED (cuanto 4)

> Documentación estructurada según **ISO/IEC/IEEE 29119**, norma vigente, que en su parte 3
> reemplazó formalmente a **IEEE 829** en 2013. Se cita 829 como antecedente: su estructura
> documental se conserva casi íntegra en 29119-3 y sigue siendo la referencia clásica en la
> enseñanza, pero la norma que se sigue aquí es la vigente.

---

## 1. Introducción

Verificar que las tres ventanas del prototipo se comportan igual en los navegadores que usa el
segmento objetivo: sostenedores y equipos directivos de establecimientos subvencionados.

## 2. Matriz de compatibilidad

| Motor | Navegador | Versiones | Justificación |
|-------|-----------|-----------|---------------|
| Blink | Chrome | dos últimas | Mayoritario en el segmento educacional chileno |
| Blink | Edge | dos últimas | Preinstalado en el parque de equipos institucionales con Windows |
| Gecko | Firefox | dos últimas | Segundo motor: detecta dependencias de implementación, no de estándar |
| WebKit | Safari | última | Solo si algún sostenedor opera en macOS |

Tres motores distintos, no tres navegadores del mismo motor: probar Chrome y Edge por separado
aporta poco porque comparten Blink. El valor está en Gecko y WebKit.

## 3. Resoluciones objetivo

| Resolución | Perfil |
|------------|--------|
| 1366 × 768 | Portátil institucional típico. **Es el caso de diseño**, no el mejor caso |
| 1920 × 1080 | Escritorio de sostenedor |
| 1280 × 720 | Mínimo declarado |

Escritorio es el objetivo. Tablet se declara como **degradación aceptable**: debe ser legible,
no necesariamente idéntico. Móvil queda fuera de alcance declarado.

## 4. Elementos a probar

| ID | Elemento | Por qué se rompe entre motores |
|----|----------|-------------------------------|
| CMP-01 | Renderizado SVG de los gráficos Recharts | Diferencias de cálculo de `viewBox` y de fuentes |
| CMP-02 | Control deslizante del simulador | Eventos de puntero implementados distinto |
| CMP-03 | Formato numérico en español de Chile | Coma decimal contra punto según `Intl` |
| CMP-04 | Carga inicial y primera pintura | Presupuesto de rendimiento |
| CMP-05 | Navegación por teclado | Orden de foco y `:focus-visible` |
| CMP-06 | Contraste de texto sobre fondo | Cumplimiento de WCAG AA |

## 5. Enfoque: híbrido

**Automatizado.** Humo en los tres motores con Playwright, que los instala con un comando y sin
licencia: carga de las tres ventanas, renderizado de los gráficos y una interacción del
simulador. Cubre CMP-01, CMP-02 y CMP-04.

**Manual documentado.** Matriz con capturas para CMP-03, CMP-05 y CMP-06, donde el juicio visual
es más barato y más confiable que una aserción automatizada.

## 6. Accesibilidad

Dentro de alcance: contraste y navegación por teclado, porque son baratos y de alto impacto.
Fuera de alcance declarado: compatibilidad con lectores de pantalla, que exige un ciclo de
pruebas con usuarios que el proyecto excluye explícitamente.

## 7. Rendimiento

Umbral simple: **primera pintura con contenido bajo 3 segundos** en el navegador más lento de la
matriz, con la API respondiendo localmente. Un plan de carga completo sería desproporcionado
para un prototipo de tres ventanas.

## 8. Criterios de aprobación y suspensión

**Aprobación.** Los seis elementos verificados en los tres motores a 1366 × 768; ninguna
diferencia que impida completar el flujo; el umbral de primera pintura se cumple.

**Suspensión.** Si un motor no logra renderizar los gráficos, se detiene la campaña en ese motor
y se documenta como incompatibilidad, no como fallo de caso.

## 9. Entregables

`tests/compatibilidad/` con las pruebas de Playwright · matriz manual con capturas por navegador
y resolución · registro de incompatibilidades con su decisión: se corrige, se degrada o se
declara fuera de soporte.

## 10. Estado actual

**No implementado.** La estructura de carpetas existe; falta instalar Playwright, escribir el
humo de los tres motores y levantar la matriz manual.

## 11. Riesgo declarado

El endpoint de simulación tarda **4,6 segundos** por las 54 inferencias que ejecuta. Eso excede
el umbral de primera pintura y es limitación conocida documentada del backend, no un defecto de
compatibilidad. La interfaz debe mostrar un indicador de progreso; las pruebas de este plan no
lo cuentan como fallo.
