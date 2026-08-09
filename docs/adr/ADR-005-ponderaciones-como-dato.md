# ADR-005 — Almacenar las ponderaciones oficiales como dato de catalogo

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
Las ponderaciones de los seis factores estan fijadas por norma y cambian por decision
administrativa. Incrustarlas en el codigo convierte cada cambio normativo en un despliegue,
y las expone al principio CACE.

## Decision
Las ponderaciones viven en `contratos/catalogo_factores.json` y en la tabla `core.factor_sned`.
El indice se reconstruye por agregacion con producto. La vista `hechos.v_indicer_reconstruido`
contrasta permanentemente el valor calculado con el oficial.

## Evidencia
Aplicar las ponderaciones documentadas a los valores reales de los seis factores reprodujo
el indice ministerial con **R2 = 1,0000 y MAE = 0,000**: la formula publicada no tiene
ajustes ni escalamientos no declarados.

## Alternativas descartadas
- **Constantes en el codigo.** Descartado: convierte cada cambio normativo en un despliegue y
  expone la formula al principio CACE.
- **Variables de entorno.** Descartado: seis pesos con restriccion de suma no son configuracion
  de despliegue, son dato de dominio con invariante propia; el entorno no puede validarla.
- **Tabla sin invariante declarada.** Descartado: sin el disparador diferido que verifica la
  suma, una actualizacion parcial dejaria el catalogo en estado invalido sin aviso.

## Consecuencias
- Un cambio normativo es un `UPDATE`, no un cambio de codigo.
- La discrepancia de la vista de auditoria funciona como alarma temprana de cambio normativo.

## Consecuencias negativas
- El catalogo en archivo y la tabla pueden divergir. Ocurre en la practica, y por eso la
  inicializacion valida la correspondencia y aborta en lugar de repararla en silencio.
- Una actualizacion incorrecta de la tabla altera **todos** los indices reconstruidos a la vez,
  sin que ninguna prueba unitaria lo detecte: la deteccion depende de la vista de auditoria.
- La invariante de suma obliga a que toda actualizacion ocurra dentro de una sola transaccion,
  restriccion que no es evidente para quien edite la tabla por primera vez.

