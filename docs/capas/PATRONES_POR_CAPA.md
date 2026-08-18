# Los patrones de diseño, ordenados por capa

Identificador del documento: **PC-SNED-01**
Fecha: **15 de agosto de 2026**

`docs/PATRONES_DE_DISENO.md` documenta doce patrones aplicados con su justificación detallada, su
fuente bibliográfica y el código donde vive cada uno. Los ordena **por cuanto**. Este documento los
ordena **por capa**, que es la otra pregunta razonable: qué patrón resuelve qué problema en qué
nivel del sistema.

No hay patrones nuevos aquí. Es el mismo conjunto visto desde el otro eje. Para la justificación
completa de cada uno, la referencia sigue siendo `PATRONES_DE_DISENO.md`.

---

## 1. La tabla

| Capa | # | Patrón | Categoría | Fuente | Qué resuelve en esta capa |
|------|---|--------|-----------|--------|---------------------------|
| **Presentación** | P7 | **Facade** | Estructura (GoF) | Gamma et al. (1994) | El router habla con una sola fachada, `ServicioDePrediccion`, en vez de coordinar motor, repositorio y reglas |
| **Aplicación** | P4 | **Specification** | DDD | Evans (2003) | Las reglas de alerta son especificaciones componibles con Y/O/NO: agregar una no toca el flujo de evaluación |
| **Aplicación** | P5 | **Decorator** | Estructura (GoF) | Gamma et al. (1994) | La auditoría de toda inferencia (CTRL-05) y la caché se componen en tiempo de ejecución sin contaminar las estrategias |
| **Dominio** | P1 | **Strategy** | Comportamiento (GoF) | Gamma et al. (1994) | El motor se expone como `EstrategiaPredictiva`: bosque aleatorio o red neuronal son intercambiables sin que nadie fuera del dominio se entere |
| **Dominio** | P6 | **Factory Method** | Creación (GoF) | Gamma et al. (1994) | La estrategia se resuelve por clave, no por condicionales dispersos |
| **Dominio** | P8 | **Builder** | Creación (GoF) | Gamma et al. (1994) | Un escenario contrafactual se construye paso a paso y validado, en vez de copiar diccionarios a mano |
| **Dominio** | P10 | **Registry** | Empresarial | Fowler (2002) | El catálogo de factores y el de modelos son accesibles por clave sin variables globales dispersas. Es lo que permite que las ponderaciones sean dato y no código |
| **Persistencia** | P2 | **Repository** | Empresarial | Fowler (2002) | La capa de aplicación pide establecimientos a un puerto; que detrás haya Parquet o PostgreSQL es una decisión de despliegue |
| **Persistencia** | P11 | **Adapter** | Estructura (GoF) | Gamma et al. (1994) | Cada implementación concreta del puerto: dos adaptadores, 141 llamadas comparadas, cero divergencias |
| **Persistencia** | P3 | **Template Method** | Comportamiento (GoF) | Gamma et al. (1994) | Doce fuentes MINEDUC con el mismo esqueleto de ingesta y solo la lectura concreta distinta |
| **Persistencia** | P9 | **Virtual Proxy / Lazy Load** | Estructura (GoF); Fowler (2002) | Gamma et al. (1994) | Artefactos de 60 MB que se cargan cuando se usan y no al arrancar |
| **Transversal** | P12 | **Pipes and Filters** | Arquitectura | Buschmann et al. (1996) | No pertenece a una capa: es el estilo del cuanto de ingesta completo. Ver sección 3 |

## 2. Lo que la tabla muestra al leerla por columnas

**El dominio concentra cuatro patrones y los cuatro son de creación o de comportamiento.** Ninguno
es estructural, y eso no es casualidad: la capa que no depende de nadie no necesita adaptar nada.

**La persistencia concentra los estructurales.** Repository, Adapter, Template Method y Virtual
Proxy son todos, en el fondo, la misma respuesta a la misma fuerza: el medio de almacenamiento y el
formato de la fuente cambian, y el dominio no debe enterarse.

**La presentación tiene exactamente uno.** Es un buen indicio. Una capa de presentación con muchos
patrones suele ser una capa de presentación que está haciendo el trabajo de otra.

**Specification aparece en aplicación pero nace en dominio.** Su puerto vive en
`compartido/especificacion.py` y lo usan tanto las reglas de cuarentena de la ingesta como las
reglas de alerta del servicio. Se lista en aplicación porque ahí se evalúa, no porque ahí se
defina.

## 3. El que no cabe, y por qué se declara en vez de forzarlo

**P12 · Pipes and Filters no es un patrón de capa.** Es el estilo arquitectónico interno del cuanto
de ingesta: leer → normalizar → filtrar → particionar → persistir, una secuencia unidireccional
donde cada etapa transforma sin conocer a las demás.

Se podría escribir que «pertenece a la capa de persistencia» y la tabla quedaría completa y
simétrica. Sería falso. Una tubería no es un apilamiento: en las capas la dependencia va hacia
abajo y el control vuelve hacia arriba; en una tubería el flujo no vuelve. Meterlo a la fuerza
haría la tabla más ordenada y el documento menos cierto.

Lo mismo, en menor grado, ocurre con P10 · Registry, que en `PATRONES_DE_DISENO.md` está
documentado junto a Factory Method como el mecanismo de microkernel de Q2. Aquí figura en dominio
porque el catálogo de factores es una regla de dominio; visto desde el otro eje es topología de
microkernel. Los dos niveles describen la misma estructura con vocabularios distintos.

## 4. Patrones descartados

`PATRONES_DE_DISENO.md` §3 documenta doce patrones evaluados y **descartados**, con el motivo de
cada descarte. Esa sección no se reordena aquí: un patrón que no se aplicó no tiene capa.

Vale la pena conservarla a la vista en una defensa. Un catálogo donde todo se aplicó es un catálogo
que no eligió.

## 5. Historial de modificaciones

| Fecha | Sección | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-15 | — | Documento nuevo | Los doce patrones estaban mapeados por cuanto; faltaba el mapeo por capa |
