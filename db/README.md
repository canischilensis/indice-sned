# Modelo físico — derivación desde el modelo conceptual

Este esquema **no se improvisó**: se obtuvo aplicando las reglas estándar de mapeo
entidad-relación → relacional sobre el diagrama ER del proyecto. Este documento deja
constancia de esa derivación, que es la evidencia del paso conceptual → físico.

## Orden de aplicación

```bash
docker compose up -d postgres
python scripts/inicializar_bd.py          # esquemas → semillas → factores → vistas
python scripts/inicializar_bd.py --dry-run # solo lista los archivos, no conecta
```

Todo el DDL es idempotente: `IF NOT EXISTS`, `CREATE OR REPLACE`, `ON CONFLICT`.

## Los cuatro esquemas

| Esquema | Origen | Contenido |
|---------|--------|-----------|
| `core` | **Derivado del ER** | Entidades fuertes, entidad asociativa y catálogos de normalización |
| `hechos` | **Derivado del ER** | Entidades débiles con clave compuesta. Formato largo |
| `ml` | No proviene del ER | Registro de modelos, inferencias y explicaciones (CTRL-05) |
| `app` | No proviene del ER | RBAC, simulaciones y auditoría de acceso (CTRL-04) |

Que `ml` y `app` no deriven del diagrama es deliberado y conviene declararlo: son
infraestructura, no dominio del problema. Así la correspondencia entidad → tabla sigue
siendo uno a uno.

---

## Parte 1 · Entidades del diagrama → tablas

| # | Entidad (ER) | Tabla (SQL) | Clave primaria | Regla aplicada |
|---|--------------|-------------|----------------|----------------|
| 1 | ESTABLECIMIENTO | `core.establecimiento` | `rbd` | Entidad fuerte → tabla; atributo subrayado → PK |
| 2 | PERIODO | `core.periodo` | `periodo_id` | Entidad fuerte → tabla |
| 3 | COMUNA | `core.comuna` | `cod_comuna` | Entidad fuerte → tabla |
| 4 | GRUPO_HOMOGENEO | `core.grupo_homogeneo` | `cluster_codigo` | Entidad fuerte → tabla |
| 5 | FACTOR_SNED | `core.factor_sned` | `factor_cod` | Entidad fuerte → tabla (catálogo) |
| 6 | ESTABLECIMIENTO_PERIODO | `core.establecimiento_periodo` | `rbd + periodo_id` | Entidad asociativa (M:N) → tabla intermedia |
| 7 | RESULTADO_SNED | `hechos.sned_resultado` | `rbd + periodo_id` | Entidad débil → PK compuesta |
| 8 | VALOR_FACTOR | `hechos.sned_factor` | `rbd + periodo_id + factor_cod` | Entidad débil → PK compuesta con FK al padre |
| 9 | MEDICION_SIMCE | `hechos.simce_medicion` | `rbd + periodo_id + nivel_cod + asignatura_cod` | Entidad débil → PK compuesta de 4 campos |
| 10 | MEDICION_IDPS | `hechos.idps_medicion` | `rbd + periodo_id + nivel_cod + dimension_cod` | Entidad débil → PK compuesta de 4 campos |
| 11 | EVENTO_SIE | `hechos.sie_evento_agregado` | `rbd + ventana_id + tipo_evento_cod` | Entidad débil → PK compuesta |
| 12 | INDICADOR_ANUAL | `hechos.indicador_anual` | `rbd + anio + indicador_cod` | Entidad débil → PK compuesta |

**12 entidades → 12 tablas.** Correspondencia uno a uno.

---

## Parte 2 · Tablas que no están en el ER

**Nueve** tablas de catálogo surgen al implementar, no al modelar el dominio. (El Anexo de
mapeo dice "ocho" en el párrafo introductorio de su sección 3, pero su Tabla A3 lista nueve:
el recuento del párrafo quedó de una versión previa donde región y provincia compartían fila.)

| Tabla | Por qué existe |
|-------|----------------|
| `core.region`, `core.provincia` | Descomposición de la jerarquía geográfica implícita en COMUNA |
| `core.dependencia` | Normaliza el atributo `dependencia` |
| `core.nivel_educativo` | Normaliza el atributo `nivel` de SIMCE e IDPS |
| `core.asignatura` | Normaliza `asignatura` |
| `core.dimension_idps` | Normaliza `dimension` |
| `core.tipo_indicador` | Normaliza `tipo_indicador` |
| `core.tipo_evento_sie` | Normaliza `tipo_evento` |
| `core.ventana_sie` | Normaliza `ventana_temporal` y codifica la regla anti-fuga (CTRL-02) |

**El patrón:** cada atributo que en el ER era texto con valores repetidos pasa a ser tabla de
catálogo más clave foránea. Es lo que lleva el esquema a tercera forma normal: se evita repetir
`"4to Básico"` veinte mil veces.

---

## Parte 3 · Tratamiento de cada tipo de atributo

| Atributo | Entidad | Resolución en SQL |
|----------|---------|-------------------|
| `rbd` **[PK]** | ESTABLECIMIENTO | `INTEGER PRIMARY KEY` |
| `nombre_completo` **[C]** compuesto | ESTABLECIMIENTO | Se descompone; solo se materializa `nombre` |
| `dependencia` **[O]** opcional | ESTABLECIMIENTO_PERIODO | `SMALLINT` sin `NOT NULL` + FK a catálogo |
| `es_rural` **[O]** opcional | ESTABLECIMIENTO_PERIODO | `BOOLEAN` sin `NOT NULL` |
| `duracion` **[D]** derivado | PERIODO | **No se almacena** — `anio_fin - anio_inicio + 1` |
| `indicer` **[D]** derivado | RESULTADO_SNED | **Se almacena** (valor oficial del Estado) + vista `v_indicer_reconstruido` para auditarlo |
| `posicion_en_grupo` **[D]** derivado | RESULTADO_SNED | **No se almacena** — la calcula `v_ranking_intra_cluster` |
| `puntaje` **[O]** opcional | MEDICION_SIMCE | `NUMERIC` sin `NOT NULL`; si no se imparte el nivel, no hay fila |
| `valor` **[O]** opcional | MEDICION_IDPS | `NUMERIC` sin `NOT NULL`; la ausencia se representa omitiendo la fila |
| `ponderacion` | FACTOR_SNED | `NUMERIC(4,3)` + trigger que valida que sumen 1,000 |

Sobre `indicer` hay dos opciones legítimas: la purista (no guardarlo, calcularlo siempre) y la
pragmática (guardarlo y auditar). **Se adoptó la pragmática**, porque el índice oficial lo emite
el Estado y debe conservarse tal cual, no recalcularse. La vista existe para verificar que ambos
coinciden — que es exactamente el control que arrojó R² = 1,0000.

La vista usa la nomenclatura del Anexo (`indicer_calculado`, `indicer_oficial`, `discrepancia`
en valor absoluto) y añade tres columnas de apoyo que el Anexo no declara: el signo de la
desviación, la etiqueta del período y el conteo de factores, que debe ser siempre seis.

---

## Parte 4 · Materialización de las relaciones

| Relación | Cardinalidad | Implementación |
|----------|--------------|----------------|
| COMUNA — *ubica* — ESTABLECIMIENTO | 1:N | `cod_comuna` como FK en `establecimiento` |
| ESTABLECIMIENTO — *obtiene* — RESULTADO_SNED | 1:N | `rbd` como FK en `sned_resultado` |
| PERIODO — *enmarca* — RESULTADO_SNED | 1:N | `periodo_id` como FK en `sned_resultado` |
| GRUPO_HOMOGENEO — *agrupa* — RESULTADO_SNED | 1:N | `cluster_codigo` como FK en `sned_resultado` |
| RESULTADO_SNED — *se descompone en* — VALOR_FACTOR | 1:N identificadora | FK compuesta `(rbd, periodo_id)` + `ON DELETE CASCADE` |
| FACTOR_SNED — *tipifica* — VALOR_FACTOR | 1:N | `factor_cod` como FK |
| ESTABLECIMIENTO — *rinde* — MEDICION_SIMCE | 1:N identificadora | `rbd` dentro de la PK compuesta |
| ESTABLECIMIENTO ↔ PERIODO | M:N | Tabla intermedia `establecimiento_periodo` |

`ON DELETE CASCADE` aparece **solo** en las relaciones identificadoras: es la traducción literal
del rombo doble. Una entidad débil no puede existir sin su padre.

---

## Parte 5 · Dos decisiones que un evaluador preguntará

### Por qué `cluster_codigo` está en RESULTADO_SNED y no en ESTABLECIMIENTO

Porque en el diagrama la relación *agrupa* conecta GRUPO_HOMOGENEO con **RESULTADO_SNED**, no
con el establecimiento. No es una sutileza de modelado: el **35,1 % de los establecimientos
cambia de agrupación entre ciclos**. Almacenar el grupo como atributo invariante del
establecimiento falsearía el resultado precisamente en la variable que determina la selección
del beneficio.

### Por qué la especialización no aparece en el SQL

La jerarquía ESTABLECIMIENTO → ACADÉMICO / ESPECIAL admite tres estrategias de mapeo:

1. Una tabla por subtipo
2. Tabla única con columna discriminadora
3. Colapso al subtipo relevante

Se aplicó la **tercera**. Redacción sugerida para el informe:

> La especialización disjunta entre establecimientos académicos y especiales se modela en el
> nivel conceptual pero no se materializa en el esquema físico, dado que el alcance del sistema
> se restringe al subtipo académico. Los establecimientos del subtipo especial fueron excluidos
> durante la depuración.

---

## Parte 6 · Verificación de correspondencia

Controles ejecutados contra PostgreSQL 16 con el DDL aplicado:

| Pregunta de verificación | Resultado |
|--------------------------|-----------|
| ¿Cada entidad tiene exactamente una tabla? | Sí, 12 de 12 |
| ¿Cada atributo subrayado es PRIMARY KEY? | Sí |
| ¿Cada atributo derivado está ausente o auditado? | Sí — `duracion` y `posicion_en_grupo` ausentes; `indicer` auditado |
| ¿Cada rombo tiene su FOREIGN KEY? | Sí — 34 claves foráneas |
| ¿Cada rombo doble tiene ON DELETE CASCADE? | Sí — verificado: borrar el resultado eliminó sus 6 factores |
| ¿Cada entidad débil tiene PK compuesta? | Sí — **6 de 6** entidades débiles |
| ¿Cuántas PK compuestas hay en total? | **7** — las 6 débiles más `establecimiento_periodo`, que es entidad *asociativa*, no débil |
| ¿El trigger de ponderaciones rechaza sumas distintas de 1,0? | Sí — `ERROR: las ponderaciones vigentes suman 1.130` |
| ¿La vista de auditoría detecta discrepancias? | Sí — `-1,6500` con datos desalineados, `0,0000` al corregir |
| ¿`REFRESH MATERIALIZED VIEW CONCURRENTLY` funciona? | Sí — el índice único lo habilita |

Recuento final: **29 tablas** (core 15, hechos 6, ml 4, app 4), **2 vistas**, **1 vista
materializada**, **34 claves foráneas**.

Las 21 tablas de `core` + `hechos` corresponden exactamente a **12 entidades del ER + 9
catálogos de normalización**. Las 8 restantes pertenecen a `ml` y `app`, que no derivan del
diagrama: son infraestructura de trazabilidad y de aplicación. Conviene declararlo al presentar
el esquema, porque de lo contrario el "12 de 12" de la verificación parece no cuadrar con las
29 tablas que muestra la base.

Sobre las claves foráneas: el Anexo cuenta **11 relaciones conceptuales**; el esquema tiene 34
restricciones `FOREIGN KEY` porque incluye además las que apuntan a los catálogos de
normalización y las de los esquemas `ml` y `app`. No es una discrepancia, son denominadores
distintos.

---

## Parte 8 · Contraste con el modelo físico (drawio)

El diagrama de modelo físico declaraba diez columnas que el DDL no tenía. **Todas fueron
adoptadas** y verificadas contra PostgreSQL 16.

| Columna | Tabla | Qué aporta |
|---------|-------|------------|
| `anio_aplicacion` | `hechos.simce_medicion` | Año real de rendición, fuera de la llave |
| `fecha_alta`, `fecha_baja` | `core.establecimiento` | Ciclo de vida: explica por qué un RBD desaparece entre bienios sin que sea error de cruce |
| `recibe_sned` | `core.dependencia` | Regla de negocio en el esquema: el particular pagado no recibe subvención |
| `factor_asociado` | `core.tipo_indicador` | Linaje: qué factor del índice alimenta cada indicador |
| `factor_asociado` | `core.tipo_evento_sie` | Ídem para los eventos de la Superintendencia |
| `familia` | `core.tipo_evento_sie` | Agrupa denuncia / proceso / mediación, con `CHECK` |
| `nombre` | `core.tipo_indicador` | Etiqueta legible |
| `id_oficial` | `core.dimension_idps` | Código del organismo emisor |
| `fuente_oficial` | `core.factor_sned` | Trazabilidad normativa de la ponderación |

### El linaje llevado al esquema

`factor_asociado` es la aportación más valiosa del diagrama: la relación indicador → factor
existía solo implícita, dentro del motor desagregado. Ahora es consultable y la refuerza una
clave foránea. Mapeo sembrado:

| Factor | Indicadores |
|--------|-------------|
| IGUALDR | `tasa_retiro`, `n_vulnerables`, `n_beneficiarios_sep`, `tiene_convenio_sep`, `ive_basica`, `ive_media`, `ive_consolidado` |
| MEJORAR | `n_docentes`, `horas_docentes`, `n_directivos`, `n_asistentes` |
| EFECTIVR | `tasa_aprobacion`, `tasa_reprobacion` |
| (contexto) | `matricula_total`, `cursos_total` — no alimentan ningún factor |

Y en eventos SIE: las familias `denuncia` y `proceso` apuntan a IGUALDR, fundado en que la
restricción documentada de ese factor menciona la desagregación de sanciones. La familia
`mediacion` queda **sin mapear** a propósito: no hay base documental para asignarla, y un
`NULL` explícito es preferible a una atribución inventada. Corregirlo es un `UPDATE`.

### Cambio de orden en la inicialización

`core.tipo_indicador` y `core.tipo_evento_sie` ahora tienen clave foránea hacia
`core.factor_sned`, de modo que el catálogo de factores debe sembrarse **antes** que las demás
semillas. El orden en `scripts/inicializar_bd.py` pasó a ser:

    esquemas → catálogo de factores → semillas → vistas

### `core.ventana_sie` cambió de significado

Antes estaba atada a un período (`periodo_id`) con una ventana por bienio. Ahora es autónoma y
codifica la **partición temporal del experimento**: `SIE 2016-2017` para entrenamiento y
`SIE 2018-2022` para validación. Se conserva `fecha_corte` además de `anio_fin`, porque CTRL-02
se verifica con precisión de día: un evento del 30 de diciembre y otro del 2 de enero caen en
ventanas distintas, y el año solo no permite distinguirlos.

### Supuesto declarado sobre la llave de SIMCE

La llave es `(rbd, periodo_id, nivel_cod, asignatura_cod)` y `anio_aplicacion` queda fuera. Eso
implica que **se registra una sola aplicación SIMCE por período, nivel y asignatura**: la que el
SNED considera para ese bienio. Una segunda aplicación del mismo nivel y asignatura dentro del
período es rechazada por la clave primaria — comportamiento verificado, no accidental. El
supuesto está declarado en un `COMMENT` sobre la columna.

### Verificaciones ejecutadas

| Control | Resultado |
|---------|-----------|
| FK de linaje rechaza un factor inexistente | `ERROR: violates foreign key constraint "tipo_indicador_factor_asociado_fkey"` |
| `CHECK` de familia rechaza una familia inventada | `ERROR: violates check constraint "tipo_evento_sie_familia_check"` |
| `fecha_baja` anterior a `fecha_alta` es rechazada | `ERROR: violates check constraint "establecimiento_check"` |
| Segunda aplicación SIMCE en el mismo período colisiona | `ERROR: duplicate key value violates unique constraint` |

---

## Parte 7 · Contraste con el diagrama ERDPlus

Verificado contra la exportación del diagrama. Las 12 entidades tienen su tabla y las 11
relaciones su clave foránea. Estas son las diferencias detectadas y cómo se resolvieron.

### Resueltas en el esquema

| Diferencia | Resolución |
|------------|------------|
| `es_accionable` en FACTOR_SNED no existía en el DDL | **Agregado.** `core.factor_sned.es_accionable BOOLEAN NOT NULL DEFAULT TRUE`, sembrado desde `contratos/catalogo_factores.json` |
| `tipo` en PERIODO no existía en el DDL | **Agregado.** `core.periodo.tipo` con `CHECK` sobre tres valores, reemplaza a `es_bienio_premio`, que codificaba lo mismo de forma menos general |

Criterio de `es_accionable`: el establecimiento puede influir en los insumos del factor dentro
del ciclo **y** el sistema puede simular al menos una variable que lo alimente. Es un eje
distinto de `restriccion`, que marca los factores acotados por información que solo posee el
organismo emisor. Bajo este criterio los seis factores son accionables salvo **MEJORAR**, cuya
varianza objetivo es próxima a cero: no hay nada que mover. Cambiar el criterio es un `UPDATE`,
no un despliegue.

### Resueltas en el diagrama

Corregidas en la fuente ERDPlus, de modo que diagrama y esquema quedan alineados:

| Observación | Corrección aplicada |
|-------------|---------------------|
| SIMCE se llaveaba por `anho_aplicacion` e IDPS por `periodo_id` | **Ambas usan `periodo_id`.** Elimina la inconsistencia entre entidades hermanas y permite unirlas en el mismo período sin conversión intermedia |
| IDPS estaba dibujado como rectángulo simple | **Doble rectángulo**, y el rombo *reporta* también doble: es entidad débil, su llave incluye `rbd` y no puede existir sin ESTABLECIMIENTO |
| `anho_inicio` y `anho_fin` aparecían punteados en PERIODO | **Trazo continuo.** Son atributos simples; **solo `duracion` queda derivada**, que es lo que el esquema implementa |

### Única diferencia abierta

| Artefacto | Nombre |
|-----------|--------|
| Diagrama ERDPlus | `SIMCE`, `IDPS` |
| Anexo de mapeo (Tabla A2) | `MEDICION_SIMCE`, `MEDICION_IDPS` |
| Esquema físico | `hechos.simce_medicion`, `hechos.idps_medicion` |

Los tres se refieren a la misma entidad. Conviene unificar la nomenclatura conceptual entre
diagrama y anexo; el nombre de la tabla física puede diferir del nombre de la entidad sin
problema, y de hecho la Tabla A2 ya documenta esa correspondencia.

### Columnas del esquema que el diagrama no declara

Añadidos de implementación, no de dominio. Se declaran para que el esquema no prometa menos de
lo que tiene:

| Columna | Tabla | Motivo |
|---------|-------|--------|
| `tasa_por_matricula` | `hechos.sie_evento_agregado` | Normaliza el conteo de eventos por tamaño del establecimiento |
| `nivel_ensenanza` | `core.grupo_homogeneo` | El agrupamiento oficial distingue básica de media |
| `vigente_desde`, `vigente_hasta` | `core.factor_sned` | Versionado de la normativa: permite reconstruir ciclos con ponderaciones antiguas |
| `descripcion` | `core.factor_sned` | Texto mostrado en la interfaz |
| `orden_norte_sur` | `core.region` | Ordenamiento geográfico convencional en reportes |
| `organismo` | `core.tipo_evento_sie` | Emisor del registro; hoy siempre la Superintendencia |
| `restriccion` | `core.factor_sned` | Marca los factores acotados por información no pública |

---

## Nota sobre el tipo del RBD

En el esquema físico el RBD es `INTEGER`, que es su forma canónica. La **ingesta lo lee como
texto** para no perder ceros a la izquierda durante el parseo de los archivos del MINEDUC, y
recién después lo normaliza. Son dos etapas distintas y ambas necesarias: leerlo directamente
como entero rompe silenciosamente el cruce entre fuentes. Ver
`quanta/q1_ingesta/calidad.py::normalizar_rbd`.
