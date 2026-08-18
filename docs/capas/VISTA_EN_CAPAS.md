# Vista en capas del ecosistema SNED

Identificador del documento: **VC-SNED-01**
Fecha: **15 de agosto de 2026**
Marco de referencia: Richards y Ford (2020), *Fundamentals of Software Architecture*, cap. 10;
Fowler (2002), *Patterns of Enterprise Application Architecture*, cap. 1.

Este documento describe el sistema **por capas**. No reemplaza a `ARQUITECTURA_AD_HOC.md`, que lo
describe por cuantos hexagonales: son dos vistas del mismo código, y la sección 6 explica por qué
ninguna sobra.

**Nada de lo que aquí se afirma se declara sin comprobarlo.** La sección 5 registra tres puntos
donde la clausura de capas no se cumple, encontrados al revisar las importaciones reales.

---

## 1. Las cuatro capas

| # | Capa | Responsabilidad | Dónde vive |
|---|------|-----------------|------------|
| 1 | **Presentación** | Recibir la petición, autenticar, validar la forma y devolver una representación | `q4_cliente/` (React) · `q3_servicio/api/v1/routers/` · `q3_servicio/esquemas/` |
| 2 | **Aplicación** | Coordinar el caso de uso: orquestar dominio y persistencia, aplicar reglas de acceso | `q3_servicio/servicios/` · `q3_servicio/core/seguridad.py` |
| 3 | **Dominio** | Las reglas que serían verdaderas aunque el sistema no existiera: qué es una predicción, qué es un escenario, qué es un dato admisible | `q2_modelamiento/` · `q1_ingesta/reglas.py` · `compartido/especificacion.py` |
| 4 | **Persistencia** | Traer y guardar el dato, sea cual sea el medio | `q3_servicio/repositorios/` · `q1_ingesta/ingestor.py`, `fuentes.py` |

La capa de dominio es la única que **no importa a ninguna otra**. Es la comprobación que define si
una arquitectura en capas está bien construida o solamente bien dibujada.

## 2. La regla de dependencia

Las capas son **cerradas** (Richards y Ford, 2020, cap. 10, p. 135): una petición atraviesa todas
las capas hacia abajo y ninguna se salta. Un router no alcanza un repositorio; pide al servicio, y
el servicio pide al repositorio.

```
Presentación  ──►  Aplicación  ──►  Dominio
                        │
                        └────────►  Persistencia  ──►  Dominio
```

Por qué cerradas y no abiertas: el argumento es el **aislamiento del cambio**. Si la presentación
pudiera leer directamente de la persistencia, migrar de Parquet a PostgreSQL obligaría a tocar los
routers. Con las capas cerradas, esa migración ocurrió cambiando una sola línea de configuración, y
141 llamadas comparadas entre ambos adaptadores no arrojaron ninguna divergencia.

**Lo que verifica esta regla por máquina:** `scripts/verificar_arquitectura.py` comprueba el grafo
de dependencias entre cuantos y la prohibición de librerías por cuanto. Se ejecuta en cada
integración y hoy informa cero violaciones.

**Lo que ese script todavía no verifica:** la clausura *dentro* de Q3. El grafo entre cuantos está
automatizado; el orden interno presentación → aplicación → persistencia se revisa a mano, y por eso
existe la sección 5.

## 3. Qué le está permitido importar a cada capa

| Capa | Puede importar | Tiene prohibido |
|------|----------------|-----------------|
| Presentación | Aplicación, esquemas de entrada y salida | Repositorios, `pandas`, cualquier librería de aprendizaje automático |
| Aplicación | Dominio, contratos de persistencia | Implementaciones concretas de persistencia; conoce el puerto, no el adaptador |
| Dominio | `compartido/` y la biblioteca estándar | Todo lo demás. No conoce HTTP, ni la base de datos, ni el cliente |
| Persistencia | Dominio, `compartido/` | Aplicación y presentación. La dependencia nunca sube |

La prohibición de la tercera fila es la que sostiene el resto. `q2_modelamiento` y `q1_ingesta` no
importan `q3_servicio` en ninguna línea: se comprobó sobre el código y el resultado es limpio.

## 4. Cómo atraviesa una petición las cuatro capas

Ejemplo: `GET /api/v1/prediccion/{rbd}`.

| Paso | Capa | Qué ocurre |
|------|------|------------|
| 1 | Presentación | El router valida el RBD, resuelve el usuario del token y comprueba jurisdicción |
| 2 | Aplicación | `ServicioDePrediccion` recibe el caso de uso ya autorizado |
| 3 | Persistencia | El servicio pide las variables del establecimiento al repositorio, a través de su puerto |
| 4 | Dominio | La estrategia predictiva calcula sobre esas variables; las reglas de alerta se evalúan como especificaciones |
| 5 | Presentación | El esquema de salida convierte el resultado de dominio en JSON tipado |

El dominio aparece dos veces y en ningún momento sabe que hubo una petición HTTP. Esa es la
propiedad que la vista en capas hace visible.

## 5. Dónde la clausura no se cumple

Tres hallazgos de la revisión de importaciones del 15 de agosto de 2026. Ninguno es grave; los tres
son reales y quedan declarados en lugar de omitirse.

| # | Hallazgo | Dónde | Lectura |
|---|----------|-------|---------|
| **H-1** | Los routers importan excepciones de la capa de persistencia (`ConjuntoNoDisponible`, `EstablecimientoNoEncontrado`) | `prediccion.py`, `establecimientos.py` | La capa de presentación no accede al dato, pero sí conoce el **vocabulario de errores** de la persistencia. Es una fuga de tipos, no de datos: se traduce a códigos HTTP y no viaja hacia el cliente |
| **H-2** | `salud.py` importa `registro`, `estrategias_disponibles` y `cargar_catalogo` de `q2_modelamiento` sin pasar por la capa de aplicación | `routers/salud.py` | Es un salto real de capa: presentación alcanza dominio. Se explica porque la ruta de salud reporta el estado del sistema y no ejecuta un caso de uso, pero la excepción no estaba declarada |
| **H-3** | `explicabilidad.py` importa `variables_o_error` desde `prediccion.py` | `routers/` | Acoplamiento horizontal dentro de una misma capa, no una violación del orden. Indica una función de presentación compartida que debería vivir en un módulo común de la capa |

**Consecuencia registrada:** H-2 es el único que altera el orden de las capas. Corresponde
resolverlo exponiendo el estado del sistema a través de la capa de aplicación, o declarar la ruta
de salud como excepción explícita y verificarla. Queda como deuda documentada, no corregida en este
documento, porque este documento describe lo que hay.

## 6. Capas y hexágono no son dos arquitecturas

Es la pregunta que llega en cualquier revisión: si `ARQUITECTURA_AD_HOC.md` dice hexagonal y este
documento dice capas, ¿cuál es la arquitectura del sistema?

Las dos, porque responden preguntas distintas:

| | Vista en capas | Vista hexagonal |
|---|---|---|
| Qué pregunta responde | Cómo está **organizado** el código | Hacia dónde apuntan las **dependencias** |
| Unidad | La capa | El puerto y sus adaptadores |
| Qué hace visible | El recorrido de una petición | Qué se puede sustituir sin tocar el dominio |

Se corresponden: la capa de dominio es el interior del hexágono, y la de persistencia es un
adaptador de un puerto. Un repositorio de Parquet y uno de PostgreSQL son la misma capa y dos
adaptadores.

**Donde la correspondencia se rompe, y conviene decirlo antes de que lo pregunten.** Solo Q3 está
organizado internamente en capas. Los otros dos cuantos de servidor tienen otro estilo interno,
documentado en `ARQUITECTURA_AD_HOC.md` §3.bis:

| Cuanto | Estilo interno | Por qué no se deja partir en capas |
|--------|----------------|-----------------------------------|
| Q1 · Ingesta | Tubería y filtros | Es una secuencia unidireccional de transformaciones, no un apilamiento. Poner «capas» sobre leer → normalizar → filtrar → persistir sería renombrar etapas |
| Q2 · Modelamiento | Microkernel | Un núcleo mínimo más estrategias registradas por clave. La sustitución es lateral —una estrategia por otra—, no vertical |

Por eso la vista en capas de este documento es **del sistema completo y del recorrido de una
petición**, no de la organización interna de cada cuanto. Afirmar que el ecosistema entero es una
arquitectura de cuatro capas sería más ordenado y menos cierto.

## 7. Los patrones de diseño por capa

`PATRONES_DE_DISENO.md` documenta los doce patrones aplicados y los ordena **por cuanto**. La
reorganización por capa está en `PATRONES_POR_CAPA.md`, en esta misma carpeta.

## 8. Diagrama

Fuente en `08_capas.mmd`, en esta carpeta. Se genera con el mismo procedimiento que los otros
diagramas del proyecto, descrito en `docs/diagramas/README.md`.

## 9. Referencias

- Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.
- Richards, M. y Ford, N. (2020). *Fundamentals of Software Architecture*. O'Reilly.
- Evans, E. (2003). *Domain-Driven Design*. Addison-Wesley.

## 10. Historial de modificaciones

| Fecha | Sección | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-15 | — | Documento nuevo | La arquitectura estaba documentada por cuantos hexagonales; faltaba la vista en capas y el mapeo de patrones a capas |
| 2026-08-15 | 5 | Se registran H-1, H-2 y H-3 al verificar las importaciones reales | La clausura de capas se afirmaba en una línea de otro documento y nadie la había comprobado módulo por módulo |
