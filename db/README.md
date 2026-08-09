# Directorio `db/` — esquema de la base de datos

Contiene el modelo físico completo, versionado como DDL. La base se reconstruye desde aquí: no
hay ningún objeto en producción que no esté en estos archivos.

**El DDL es la fuente de verdad.** Si el catálogo de ponderaciones en archivo diverge de la tabla,
se corrige el archivo. `scripts/inicializar_bd.py` valida esa correspondencia y aborta con un
mensaje explícito si no se cumple.

---

## Qué hay en cada archivo

| Archivo | Contenido | Objetos que crea |
|---------|-----------|------------------|
| `esquema_sned_canonico.sql` | **Referencia.** El DDL completo del que derivan los archivos fragmentados. No se ejecuta en la inicialización; se conserva como origen | — |
| `esquemas/00_esquemas.sql` | Los cuatro espacios de nombres | `core`, `hechos`, `ml`, `app` |
| `esquemas/01_core.sql` | Catálogos y dimensiones, con sus semillas y el disparador de ponderaciones | 15 tablas |
| `esquemas/02_hechos.sql` | Entidades débiles: mediciones y resultados fechados | 6 tablas |
| `esquemas/03_ml.sql` | Registro de modelos, métricas, inferencias y deriva | 8 tablas |
| `esquemas/04_app.sql` | Usuarios, jurisdicción, simulaciones y auditoría | 8 tablas |
| `vistas/01_v_indicer_reconstruido.sql` | La fórmula oficial como consulta auditable | 1 vista |
| `vistas/02_v_ranking_intra_cluster.sql` | Posición y percentil dentro del grupo del periodo | 1 vista |
| `vistas/03_mv_matriz_entrenamiento.sql` | Lista maestra del conjunto depurado y pivote de entrenamiento | 1 tabla + 1 vista materializada |

**Total: 38 tablas** — `core` 16 (las 15 del archivo más `conjunto_entrenamiento`, que se crea con
la vista materializada porque es su dependencia), `hechos` 6, `ml` 8, `app` 8.

## Orden de ejecución

```
00_esquemas.sql
01_core.sql
02_hechos.sql       ← depende de core
03_ml.sql
04_app.sql
                    ← aquí se valida catálogo contra tabla
vistas/01, 02, 03
```

`scripts/inicializar_bd.py` ejecuta este orden. Todos los archivos usan `IF NOT EXISTS` y
`ON CONFLICT`: son reejecutables sin efecto.

## Los cuatro espacios de nombres

| Espacio | Naturaleza | ¿Deriva del modelo entidad-relación? |
|---------|-----------|-------------------------------------|
| `core` | Catálogos y dimensiones | Sí, salvo `conjunto_entrenamiento` |
| `hechos` | Entidades débiles con llave compuesta | Sí |
| `ml` | Registro de modelos y trazabilidad de inferencias | **No.** Infraestructura |
| `app` | Operación: identidad, jurisdicción, escenarios, bitácora | **No.** Infraestructura |

La distinción importa para la trazabilidad: presentar tablas de infraestructura como derivadas del
modelo conceptual sería un error de correspondencia.

## Detalles del esquema que conviene conocer antes de tocarlo

### El disparador de ponderaciones es diferido

`core.factor_sned` lleva `tg_valida_ponderaciones`, que verifica **al cierre de la transacción**
que la suma de los pesos sea exactamente 1,0.

Es diferido a propósito: durante una actualización de ponderaciones los valores intermedios no
suman uno. Una restricción inmediata haría imposible cualquier cambio normativo.

### La precisión numérica está medida, no elegida por costumbre

| Columna | Tipo | Por qué |
|---------|------|---------|
| `hechos.idps_medicion.valor` | `NUMERIC(9,6)` | Medido sobre 248.957 observaciones: seis decimales reproducen el valor de origen sin pérdida |
| `hechos.indicador_anual.valor` | `NUMERIC(14,8)` | Cocientes de enteros en doble precisión; a ocho decimales el error máximo es 5e-9 |
| `hechos.sned_factor.valor` | `NUMERIC(9,6)` | Ídem |
| `hechos.sned_resultado.indicer` | `NUMERIC(6,3)` | Escala 0-100 con tres decimales, como se publica |
| `hechos.simce_medicion.puntaje` | `NUMERIC(6,2)` | Escala 0-400 con dos decimales |

Reducir cualquiera de estas precisiones introduce un error sistemático indistinguible después de
un error de modelo.

### La ausencia de fila en eventos significa cero

`hechos.sie_evento_agregado` solo tiene filas donde hubo eventos. Los adaptadores aplican
coalescencia a cero. **No se insertan filas con conteo cero** para "completar" la tabla.

### `ml.mv_matriz_entrenamiento` no se toca

Tiene el par de mediciones estandarizadas fijado en la unión y se restringe a
`core.conjunto_entrenamiento`. Cambiar la unión cambia la población de entrenamiento y con ella
todas las métricas reportadas en la tesis.

## Verificar que la base está bien

```sql
-- 38 tablas
SELECT count(*) FROM information_schema.tables
WHERE table_schema IN ('core','hechos','ml','app');

-- las ponderaciones suman exactamente 1
SELECT sum(ponderacion) FROM core.factor_sned;

-- el índice se reconstruye desde el dato persistido
SELECT max(abs(v.indicer_calculado - r.indicer)) AS discrepancia_maxima,
       avg(abs(v.indicer_calculado - r.indicer)) AS discrepancia_media,
       count(*)                                  AS filas_comparadas
FROM   hechos.v_indicer_reconstruido v
JOIN   hechos.sned_resultado r USING (rbd, periodo_id)
WHERE  v.n_factores = 6;
```

Valores esperados: 38 tablas, suma 1,0, discrepancia máxima ≈ 0,0006 sobre ≈ 44.679 filas.

## Reglas que este esquema impone

1. **No se inventan filas.** Si una fuente no cubre un establecimiento, la fila no existe.
2. **No se persisten columnas derivadas.**
3. **Los factores y el índice oficial no son variables de entrada de ningún modelo.**
4. **La ventana temporal es dato del esquema**, no un filtro en un script.
5. **El DDL manda.** El catálogo en archivo se ajusta a la tabla, nunca al revés.

## Documentación relacionada

- `docs/diseno/DISENO_BASE_DATOS.md` — las seis decisiones de normalización, con el hallazgo que
  justifica cada una
- `docs/diagramas/00_modelo_entidad_relacion.png` — modelo conceptual
- `docs/diagramas/00_modelo_fisico_bd.drawio.png` — modelo físico
- `docs/Anexo_mapeo_conceptual_fisico.docx` — reglas de transformación entre ambos
- `docs/manuales/MANUAL_INSTALACION.md` — cómo levantar la base desde cero
