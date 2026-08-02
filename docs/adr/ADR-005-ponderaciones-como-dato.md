# ADR-005 — Almacenar las ponderaciones oficiales como dato de catalogo

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
Las ponderaciones de los seis factores estan fijadas por norma y cambian por decision
administrativa. Incrustarlas en el codigo convierte cada cambio normativo en un despliegue,
y las expone al principio CACE.

## Decision
Las ponderaciones viven en `contratos/catalogo_factores.json` y en la tabla `catalogo.factor`.
El indice se reconstruye por agregacion con producto. La vista `v_reconstruccion_indice`
contrasta permanentemente el valor calculado con el oficial.

## Evidencia
Aplicar las ponderaciones documentadas a los valores reales de los seis factores reprodujo
el indice ministerial con **R2 = 1,0000 y MAE = 0,000**: la formula publicada no tiene
ajustes ni escalamientos no declarados.

## Consecuencias
- Un cambio normativo es un `UPDATE`, no un cambio de codigo.
- La discrepancia de la vista de auditoria funciona como alarma temprana de cambio normativo.
