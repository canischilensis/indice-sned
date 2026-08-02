# ADR-004 — Conservar dos motores con propositos diferenciados

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
El simulador exige trazabilidad entre la variable que el directivo manipula y el factor
que resulta afectado. Un modelo global unico produce mejor estimacion pero es opaco
respecto de esa cadena: puede usar variables de un factor para explicar la varianza de otro.

## Decision
Mantener dos estrategias registradas:
- `desagregado`: seis modelos, uno por factor, restringidos a las variables que la norma
  declara como su insumo; el indice se reconstruye con la formula legal. **R2 = 0,583.**
- `global`: HistGradientBoosting sobre las 65 variables. **R2 = 0,637.**

## Consecuencias
- El compromiso precision-explicabilidad queda **cuantificado en 0,054 de R2**.
- El simulador usa el desagregado; el global opera como estimador de referencia.
- Costo: dos motores que mantener y dos conjuntos de artefactos en el registro.
