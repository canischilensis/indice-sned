# Diseño de la base de datos

Identificador del documento: **DB-SNED-01**

Describe el modelo físico implementado en PostgreSQL 16 y las decisiones de normalización que lo
producen. El modelo entidad-relación y el modelo físico en imagen están en `docs/diagramas/`
(`00_modelo_entidad_relacion.png` y `00_modelo_fisico_bd.drawio.png`). El anexo con el mapeo
conceptual → físico está en `docs/Anexo_mapeo_conceptual_fisico.docx`.

**El DDL manda siempre.** Cuando el catálogo en archivo y la tabla divergen, el que se corrige
es el archivo. La inicialización valida esa correspondencia y aborta con un mensaje explícito si
no se cumple; no la repara silenciosamente.

---

## 1. Estructura general

| Esquema | Tablas | Naturaleza | Origen |
|---------|--------|-----------|--------|
| `core` | 16 | Catálogos y dimensiones | 15 derivan del modelo entidad-relación; `core.conjunto_entrenamiento` es infraestructura |
| `hechos` | 6 | Entidades débiles: mediciones y resultados fechados | Modelo entidad-relación |
| `ml` | 8 | Registro de modelos, métricas, inferencias y deriva | Infraestructura, no deriva del modelo conceptual |
| `app` | 8 | Usuarios, jurisdicción, simulaciones y auditoría | Infraestructura, no deriva del modelo conceptual |
| **Total** | **38** | | |

La declaración importa: en una defensa, presentar tablas de infraestructura como si derivaran
del modelo conceptual es un error de trazabilidad. `ml` y `app` existen porque el sistema
necesita operar, no porque el dominio educativo las contenga.

## 2. Las seis decisiones de normalización

Volcar la tabla ancha del modelamiento habría perpetuado nulos estructurales y anomalías de
actualización. Cada decisión responde a un hallazgo medido:

| # | Decisión | Hallazgo que la justifica | Dónde se implementa |
|---|----------|---------------------------|---------------------|
| 1 | Formato largo para mediciones e indicadores | 68,8 % de nulos estructurales en las columnas de segundo medio | `hechos.simce_medicion`, `hechos.idps_medicion`, `hechos.indicador_anual` |
| 2 | Grupo homogéneo indexado por periodo | El 35,1 % de los establecimientos cambia de agrupación entre ciclos | `hechos.sned_resultado.cluster_codigo` con `periodo_id` en la llave |
| 3 | Ponderaciones como dato de catálogo | La fórmula oficial se verificó con R² = 1,0000 y error absoluto medio 0,000 | `core.factor_sned` + `contratos/catalogo_factores.json` |
| 4 | Dimensión de cambio lento | La migración municipal hacia los servicios locales altera la dependencia sin cambiar el identificador del establecimiento | `core.establecimiento_periodo` |
| 5 | Ventanas temporales declaradas | La regla anti-fuga debe ser estructural, no un comentario en un script | `core.ventana_sie` con fecha de corte |
| 6 | Tabla genérica de indicadores anuales | Añadir una fuente debe insertar registros, no alterar el esquema | `hechos.indicador_anual` + `core.tipo_indicador` |

## 3. Esquema `core` — catálogos y dimensiones

| Tabla | Contenido | Nota de diseño |
|-------|-----------|----------------|
| `region`, `provincia`, `comuna` | División político-administrativa | Jerarquía en tres niveles; los nombres se derivan de las fuentes de dotación docente |
| `establecimiento` | Identidad estable del establecimiento | El identificador nunca cambia, aunque cambie el sostenedor |
| `establecimiento_periodo` | Atributos que varían por ciclo: dependencia, ruralidad | Dimensión de cambio lento |
| `dependencia` | Tipo de dependencia administrativa | Incluye el servicio local de educación pública |
| `periodo` | Bienios y años de aplicación | Toda medición se fecha contra esta tabla |
| `grupo_homogeneo` | Agrupación de comparación | Indexada por periodo en los hechos, no aquí |
| `factor_sned` | Los seis factores y sus ponderaciones | **Fuente única de verdad de los pesos** |
| `nivel_educativo`, `asignatura` | Ejes de la medición estandarizada | Permiten el formato largo |
| `dimension_idps` | Dimensiones del indicador de desarrollo personal y social | Idem |
| `tipo_indicador` | Catálogo abierto de indicadores anuales | Añadir una fuente es insertar una fila aquí |
| `tipo_evento_sie`, `ventana_sie` | Tipología y ventana temporal de los eventos de fiscalización | La ventana es dato, no convención |
| `conjunto_entrenamiento` | Lista maestra del conjunto depurado | Infraestructura: fija la población del pivote de entrenamiento entre ejecuciones |

### El disparador de ponderaciones

`core.factor_sned` lleva un disparador diferido, `tg_valida_ponderaciones`, que verifica al
cierre de la transacción que la suma de los pesos sea exactamente 1,0.

Es diferido a propósito: durante una actualización de ponderaciones los valores intermedios no
suman uno, y una restricción inmediata haría imposible cualquier cambio normativo. La invariante
debe cumplirse al final de la transacción, no en cada fila.

## 4. Esquema `hechos` — entidades débiles

Todas dependen existencialmente de `establecimiento` y de `periodo` o `ventana_sie`. Ninguna
tiene identificador propio: su llave primaria es compuesta.

| Tabla | Llave | Precisión | Justificación de la precisión |
|-------|-------|-----------|------------------------------|
| `sned_resultado` | rbd + periodo | `indicer NUMERIC(6,3)` | Escala 0-100 con tres decimales, como se publica |
| `sned_factor` | rbd + periodo + factor | `valor NUMERIC(9,6)` | Seis decimales reproducen exactamente el valor de origen |
| `simce_medicion` | rbd + periodo + nivel + asignatura | `puntaje NUMERIC(6,2)` | Escala 0-400 con dos decimales |
| `idps_medicion` | rbd + periodo + nivel + dimensión | `valor NUMERIC(9,6)` | **Medido sobre 248.957 observaciones: seis decimales reproducen el valor de origen sin pérdida** |
| `sie_evento_agregado` | rbd + ventana + tipo de evento | `conteo INTEGER ≥ 0` | La ausencia de fila significa cero eventos, y el adaptador lo resuelve con coalescencia |
| `indicador_anual` | rbd + periodo + indicador | `valor NUMERIC(14,8)` | Cocientes de enteros en punto flotante de doble precisión; a ocho decimales el error máximo es 5e-9 |

La precisión no se eligió por costumbre. Se midió el viaje de ida y vuelta contra los archivos
de origen y se ajustó hasta que la diferencia fue cero. Una precisión insuficiente aquí habría
introducido un error sistemático imposible de distinguir después de un error de modelo.

## 5. Esquemas `ml` y `app`

| Esquema | Tablas | Función |
|---------|--------|---------|
| `ml` | `algoritmo`, `modelo`, `modelo_feature`, `modelo_hiperparametro`, `modelo_metrica`, `inferencia`, `inferencia_atribucion`, `drift_registro` | Materializan CTRL-05 y CTRL-03: qué modelo, con qué variables, con qué desempeño, qué predijo y si el dato se desplazó |
| `app` | `usuario`, `rol`, `usuario_establecimiento`, `sostenedor`, `simulacion`, `simulacion_ajuste`, `simulacion_resultado`, `auditoria` | Soportan la operación: identidad, jurisdicción, escenarios guardados y bitácora de acceso |

`app.usuario` está creada pero aún no se usa: el directorio de autorización vive en memoria. Es
deuda declarada, no un olvido.

## 6. Vistas

| Vista | Tipo | Función |
|-------|------|---------|
| `hechos.v_indicer_reconstruido` | Vista | Expresa la fórmula oficial como consulta auditable. Incluye el conteo de factores presentes, para poder restringir la verificación a los establecimientos con los seis |
| `hechos.v_ranking_intra_cluster` | Vista | Posición y percentil dentro del grupo del periodo: la mecánica real del beneficio |
| `ml.mv_matriz_entrenamiento` | Vista materializada | Pivote de la matriz de entrenamiento. Materializada por el costo del pivote y por la naturaleza estática del dato |

`ml.mv_matriz_entrenamiento` tiene el par de mediciones estandarizadas fijado en la unión y se
restringe a `core.conjunto_entrenamiento`. **No debe modificarse**: cambiar la unión cambiaría la
población de entrenamiento y con ella todas las métricas reportadas.

## 7. Verificación del cálculo

La propiedad que hace auditable el diseño es que el índice oficial se reconstruye desde el dato
persistido sin ejecutar código de aplicación:

```sql
SELECT max(abs(v.indicer_calculado - r.indicer)) AS discrepancia_maxima,
       avg(abs(v.indicer_calculado - r.indicer)) AS discrepancia_media,
       count(*)                                  AS filas_comparadas
FROM   hechos.v_indicer_reconstruido v
JOIN   hechos.sned_resultado r USING (rbd, periodo_id)
WHERE  v.n_factores = 6;
```

Resultado medido sobre la base cargada:

| Métrica | Valor |
|---------|-------|
| Discrepancia máxima | 0,0006 |
| Discrepancia media | 0,00025 |
| Filas comparadas | 44.679 |

La discrepancia residual es redondeo de la publicación oficial a tres decimales, no error de
modelo.

## 8. Carga de datos

`scripts/cargar_bd.py` es idempotente: copia a tabla temporal y luego inserta con resolución de
conflicto sobre la llave. Reejecutarlo sobre una base ya poblada no duplica filas ni falla.

El cargador detecta el controlador de base de datos en tiempo de ejecución, porque las dos
generaciones del adaptador de PostgreSQL exponen interfaces de copia masiva distintas. Es fea
pero necesaria: sin ella, el mismo script funciona en una máquina y falla en otra.

| Volumen cargado | Filas |
|-----------------|-------|
| Total aproximado | 838.000 |
| Comparables en la verificación del índice | 44.679 |

## 9. Reglas que el diseño impone y no negocia

1. **No se inventan filas.** Si una fuente no cubre un establecimiento, la fila no existe. La
   ausencia es información.
2. **No se persisten columnas derivadas.** Se calculan en consulta o en el motor.
3. **Los factores y el índice oficial no son variables de entrada de ningún modelo.** Serían
   fuga del objetivo.
4. **La ventana temporal es dato del esquema**, no un filtro en un script.
5. **El DDL es la fuente de verdad.** El catálogo en archivo se ajusta a la tabla, nunca al
   revés.

## 10. Orden de ejecución

```
db/esquemas/00_esquemas.sql   →  los cuatro esquemas
db/esquemas/01_core.sql       →  16 tablas de catálogo, con semillas y el disparador
db/esquemas/02_hechos.sql     →  6 entidades débiles
db/esquemas/03_ml.sql         →  8 tablas de registro de modelos
db/esquemas/04_app.sql        →  8 tablas de operación
db/vistas/01, 02, 03          →  vistas y vista materializada
```

`scripts/inicializar_bd.py` ejecuta ese orden, valida la correspondencia entre catálogo y tabla,
y solo entonces crea las vistas. `db/esquema_sned_canonico.sql` conserva el DDL de referencia
del que derivan los archivos fragmentados.
