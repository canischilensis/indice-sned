# Plan de gestión de cambios

Identificador del documento: **PGCA-SNED-01**

Define cómo se solicita, evalúa, autoriza y registra un cambio sobre la línea base. La razón de
que este plan exista en un proyecto de un solo desarrollador es concreta: **hay elementos de este
sistema cuya modificación invalida resultados ya reportados**. Sin un procedimiento, esa
invalidación ocurre sin que nadie la note.

---

## 1. Elementos bajo control de cambios

| Elemento | Ubicación | Efecto de un cambio no controlado |
|----------|-----------|-----------------------------------|
| Esquema de base de datos | `db/esquemas/` | Rompe la carga y puede alterar la precisión numérica |
| Vista materializada de entrenamiento | `db/vistas/03_*.sql` | **Cambia la población de entrenamiento y con ella todas las métricas reportadas** |
| Catálogo de ponderaciones | `contratos/catalogo_factores.json` y `core.factor_sned` | Cambia el índice reconstruido |
| Contrato de los puertos | `q2_modelamiento/contrato.py`, `q3_servicio/repositorios/contrato.py` | Rompe todos los adaptadores |
| Contrato público de la interfaz de programación | Esquemas de respuesta | Rompe el cliente |
| Artefactos de modelo | `models/registry/` | Cambia las estimaciones servidas |
| Criterios de comparación de las pruebas | `tests/paridad/` | **Puede hacer aprobar una suite que debería fallar** |
| Documentos de línea base | `docs/requisitos/`, `docs/arquitectura/` | Desalinea la trazabilidad |

## 2. Clasificación de cambios

| Tipo | Definición | Autorización | Ejemplo |
|------|-----------|--------------|---------|
| **Menor** | No altera contratos, esquema, criterios ni resultados reportados | Directa | Corregir un mensaje, añadir una prueba, mejorar documentación |
| **Mayor** | Altera un contrato, el esquema o el comportamiento observable | Requiere evaluación de impacto escrita | Añadir un campo a una respuesta, una tabla, una regla de alerta |
| **Crítico** | Puede invalidar resultados ya reportados en la tesis | Requiere evaluación **y** reejecución de las verificaciones afectadas | Cambiar la unión de la matriz de entrenamiento, las ponderaciones, la precisión de una columna, un criterio de comparación |

## 3. Cambios prohibidos sin autorización explícita

Estas restricciones se declaran aquí porque su violación es silenciosa: el sistema sigue
funcionando y los números cambian sin aviso.

| Prohibición | Motivo |
|-------------|--------|
| Modificar el DDL para acomodar el catálogo en archivo | **El DDL es la fuente de verdad.** Si divergen, se corrige el archivo. La inicialización aborta con ese mensaje |
| Modificar la unión de `ml.mv_matriz_entrenamiento` | Tiene el par de mediciones fijado; cambiarlo cambia la población y las métricas |
| Persistir columnas derivadas | Anomalías de actualización |
| Usar los seis factores, el índice oficial o la agrupación como variable de entrada | Fuga del objetivo |
| Relajar el criterio de comparación para que una prueba apruebe | Convierte la suite en teatro |
| Eliminar el adaptador de parquet | Sin segundo adaptador no hay paridad que verificar |
| Sobrescribir los artefactos serializados o los archivos columnares de origen | Son la fuente; no son regenerables sin reejecutar todo |
| Refactorizar código para que un diagrama quede más limpio | El diagrama documenta el sistema, no al revés |

## 4. Procedimiento

```
   Solicitud
       │
       ▼
  ┌─────────────┐   menor    ┌──────────────┐
  │ Clasificar  │───────────▶│  Ejecutar    │
  └──────┬──────┘            └──────┬───────┘
         │ mayor / crítico          │
         ▼                          │
  ┌─────────────────────┐           │
  │ Evaluación de       │           │
  │ impacto escrita     │           │
  └──────┬──────────────┘           │
         ▼                          │
  ┌─────────────────────┐           │
  │ Autorización        │           │
  └──────┬──────────────┘           │
         ▼                          ▼
  ┌──────────────────────────────────────┐
  │ Implementar en rama, con las pruebas │
  │ que cubran el cambio                 │
  └──────┬───────────────────────────────┘
         ▼
  ┌──────────────────────────────────────┐
  │ Compuerta de calidad (3 barreras)    │
  └──────┬───────────────────────────────┘
         ▼
  ┌──────────────────────────────────────┐
  │ Actualizar documentación afectada    │
  │ en el MISMO cambio                   │
  └──────┬───────────────────────────────┘
         ▼
     Incorporar + registrar
```

## 5. Contenido de una evaluación de impacto

Obligatoria para cambios mayores y críticos. Cinco preguntas, respuesta breve:

1. **Qué elementos de la línea base toca**, nombrados uno por uno.
2. **Qué resultados ya reportados podrían quedar inválidos**, y cuáles hay que reejecutar.
3. **Qué pruebas cubren el cambio**, y si alguna hay que escribir.
4. **Cómo se revierte** si resulta equivocado.
5. **Qué documentación queda desalineada** si no se actualiza.

Un cambio crítico cuya evaluación no puede responder la pregunta 2 no se autoriza: significa que
no se sabe qué se va a romper.

## 6. Verificaciones obligatorias por tipo de cambio

| Si el cambio toca… | Reejecutar |
|--------------------|-----------|
| Esquema o carga | Inicialización, carga completa y las tres consultas de verificación |
| Ponderaciones | Verificación del índice reconstruido y validación de suma de pesos |
| Un adaptador de repositorio | Suite de paridad completa |
| El contrato de la interfaz de programación | Prueba de contrato contra el esquema publicado y regeneración de los tipos del cliente |
| Un artefacto de modelo | Métricas del registro y verificación de aditividad |
| La matriz de entrenamiento | **Todo lo anterior**, más las métricas reportadas en la tesis |

## 7. Registro de cambios

Cada cambio incorporado deja tres rastros:

| Rastro | Dónde | Contenido |
|--------|-------|-----------|
| Confirmación en el control de versiones | Historial | Qué cambió y por qué, en una línea de asunto y un cuerpo si hace falta |
| Decisión de arquitectura, si aplica | `docs/adr/` | Contexto, alternativas evaluadas, decisión y consecuencias |
| Actualización de documento de línea base | `docs/` | En el mismo cambio, nunca después |

La regla de "en el mismo cambio" no es burocracia: documentación actualizada más tarde es
documentación que no se actualiza.

## 8. Cambios ya aplicados sobre la línea base

Registro de los cambios críticos que este proyecto ya atravesó, como precedente del procedimiento:

| Cambio | Tipo | Motivo | Verificación reejecutada |
|--------|------|--------|-------------------------|
| Precisión de las mediciones de desarrollo personal a seis decimales | Crítico | La precisión anterior truncaba el valor de origen | Viaje de ida y vuelta sobre 248.957 observaciones |
| Precisión de los indicadores anuales a ocho decimales | Crítico | Cocientes de enteros en doble precisión | Error máximo medido: 5e-9 |
| Retiro de la traducción de códigos de dependencia entre adaptadores | Crítico | El diagnóstico mostró que la diferencia era temporal, no de vocabulario | Suite de paridad completa |
| Corrección de la construcción de la matriz de variables del motor desagregado | Crítico | El motor nunca había podido predecir: los modelos esperaban las banderas de ausencia | Predicción extremo a extremo y verificación de aditividad |
| Registro de un usuario de prueba con jurisdicción real en el arnés de paridad | Mayor | La comparación operaba sobre dos listas vacías | Suite de paridad completa |
| Sustitución del identificador de demostración por uno presente en el conjunto depurado | Menor | El identificador fijado no sobrevivió a la depuración | Verificación manual en la interfaz |

Los cuatro primeros son ejemplos de la regla 2 de la política de calidad: se corrigió la causa,
no el criterio.
