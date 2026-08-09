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

## Alternativas descartadas
- **Conservar solo el motor global.** Descartado: estima mejor pero no permite trazar la
  cadena variable -> factor -> indice, que es el requisito funcional central del simulador.
- **Conservar solo el motor desagregado.** Descartado: se perderia el estimador de referencia
  contra el cual medir el costo de la explicabilidad, que es justamente el dato que hace
  defendible la decision.
- **Ensamblar ambos en una prediccion unica.** Descartado: mezclar dos estimaciones producidas
  con supuestos distintos anula la trazabilidad de las dos y no mejora ninguna.

## Consecuencias
- El compromiso precision-explicabilidad queda **cuantificado en 0,054 de R2**.
- El simulador usa el desagregado; el global opera como estimador de referencia.
- Costo: dos motores que mantener y dos conjuntos de artefactos en el registro.

## Consecuencias negativas
- **Perdida medida de 0,054 de R2** en el motor que alimenta el simulador. No es una estimacion:
  es la diferencia entre 0,637 y 0,583.
- El motor desagregado **no alcanza el umbral de 0,60** declarado en el plan de calidad, y es
  justamente el que se sirve. Corresponde declarar umbrales diferenciados por sistema.
- Dos conjuntos de artefactos que mantener, versionar y verificar.
- Los dos motores usan algoritmos distintos, lo que obliga a explicar la diferencia cada vez que
  se compara su desempeno.

