# Plan de pruebas de integración

**Identificador:** PPI-SNED-01 · **Versión:** 1.0 · **Sistema:** Ecosistema predictivo del Índice SNED

> Documentación estructurada según **ISO/IEC/IEEE 29119**, norma vigente, que en su parte 3
> reemplazó formalmente a **IEEE 829** en 2013. Se cita 829 como antecedente: su estructura
> documental se conserva casi íntegra en 29119-3 y sigue siendo la referencia clásica en la
> enseñanza, pero la norma que se sigue aquí es la vigente.

---

## 1. Introducción

Verificar que los cuatro cuantos intercambian información correctamente a través de sus
fronteras declaradas. No se prueba aquí el comportamiento interno de cada cuanto —eso es
responsabilidad de las pruebas unitarias— sino el **contrato entre ellos**.

La arquitectura hexagonal hace que estas fronteras sean explícitas: cada una es un puerto con
sus adaptadores, y ahí es donde una integración se rompe.

## 2. Elementos a probar

| ID | Integración | Frontera |
|----|-------------|----------|
| INT-01 | Q1 → Q2 | El parquet producido por la ingesta alimenta al motor |
| INT-02 | Q2 → Q3 | El puerto `EstrategiaPredictiva` tras una petición HTTP |
| INT-03 | Q3 → PostgreSQL | El puerto `RepositorioEstablecimientos` contra la base real |
| INT-04 | Q3 → Q4 | El contrato JSON que consume la interfaz |
| INT-05 | Parquet ↔ PostgreSQL | Paridad entre los dos adaptadores del mismo puerto |

## 3. Elementos que NO se prueban

La ingesta desde los sitios del MINEDUC y de la Superintendencia. Son fuentes externas sin
disponibilidad garantizada ni respuesta determinista: probarlas haría la suite dependiente de
un servicio de terceros. Se sustituyen por muestras recortadas versionadas.

## 4. Enfoque (ISO 29119, diseño de casos)

| Técnica | Dónde se aplica |
|---------|-----------------|
| Prueba de contrato | INT-02 e INT-04: la respuesta se valida contra el esquema OpenAPI generado |
| Partición de equivalencia | INT-03: RBD existente, inexistente, no numérico |
| Análisis de valores límite | INT-01: establecimiento sin medición de 2° medio, con los seis factores, con factores ausentes |
| Prueba comparativa | INT-05: mismas llamadas contra ambos adaptadores, comparación campo por campo |

## 5. Criterios de aprobación y suspensión

**Aprobación.** Las cinco integraciones ejecutan sin error; la paridad INT-05 da cero
divergencias sobre las 141 llamadas; la reconstrucción del índice arroja discrepancia máxima
bajo 0,001 sobre los establecimientos con los seis factores.

**Suspensión.** Se detiene la campaña si la compuerta de fronteras de cuantos falla: significa
que un cuanto importa lo que no debe, y ninguna prueba de integración posterior es interpretable.

**Reanudación.** Tras restablecer las fronteras y volver a ejecutar `verificar_arquitectura.py`.

## 6. Entregables

`tests/integracion/` con los casos ejecutables · `tests/paridad/` con las respuestas congeladas
de ambos adaptadores · el reporte de `pytest` archivado por Sprint como acta.

## 7. Tareas, entorno y responsabilidades

PostgreSQL 16 con el esquema aplicado y cargado. Las pruebas que lo requieren llevan el
marcador `requiere_bd` y se omiten cuando no está disponible, de modo que la suite sigue siendo
ejecutable en una máquina recién clonada.

Ejecución: en cada Sprint Review, como compuerta 2 de la Definición de Terminado. Responsable:
el tesista. Validador: el profesor guía.

## 8. Riesgos

| Riesgo | Mitigación |
|--------|-----------|
| Los artefactos `.joblib` no se versionan y pesan 210 MB | Las pruebas unitarias usan dobles; solo INT-02 carga un artefacto real y está marcada como lenta |
| El cálculo de Shapley es costoso | Presupuesto explícito de 2 s por explicación, verificado una sola vez |
| Deriva entre el JSON de contrato y la tabla | `inicializar_bd.py` valida y falla si difieren |

## 9. Hallazgo de INT-04

Al escribir la prueba de contrato se descubrio que **dos de las seis rutas que consume la
interfaz devolvian `dict` sin modelo de respuesta**: `/establecimientos` y
`/establecimientos/{rbd}/ranking`. En el esquema OpenAPI aparecian como
`additionalProperties: true`, que acepta cualquier cosa. Un cliente TypeScript no puede generar
tipos desde eso: no es un contrato laxo, es la ausencia de contrato.

Se agregaron `RespuestaEstablecimientos` y `RespuestaRanking`. Las seis rutas quedan tipadas.

La prueba incluye ademas una verificacion de si misma
—`test_la_validacion_del_contrato_rechaza_cuerpos_que_no_cumplen`— porque la primera version
validaba contra esquemas vacios y pasaba sin comprobar nada.

## 10. Estado actual

| ID | Estado | Evidencia |
|----|--------|-----------|
| INT-01 | Cubierto | `tests/integracion/q1/test_pipeline_calidad.py` |
| INT-02 | Cubierto | `tests/integracion/q3/test_api_y_rbac.py` |
| INT-03 | Cubierto | Adaptador PostgreSQL verificado contra la base cargada |
| INT-04 | Cubierto | `tests/integracion/q3/test_contrato_openapi.py` |
| INT-05 | Cubierto | 141 llamadas, 0 divergencias, ejecutable en CI |
