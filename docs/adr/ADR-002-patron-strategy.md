# ADR-002 — Encapsular el motor predictivo tras el Patron Strategy

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
El teorema de la ausencia de almuerzo gratuito impide saber a priori que arquitectura
sera superior. El proyecto necesitaba comparar tres familias algorItmicas y, ademas,
sobrevivir a futuras migraciones ML -> DL sin rehacer la interfaz.

## Decision
Definir `EstrategiaPredictiva` en `q2_modelamiento/contrato.py` como unica superficie
publica del motor. La resolucion concreta se hace en `fabrica.obtener_estrategia()`.

## Alternativas descartadas
- **Herencia desde una clase base concreta:** acopla la interfaz al detalle de sklearn.
- **Exponer el estimador directamente:** filtra `predict()` y el formato de features al cuanto 3.

## Consecuencias
- Verificado empiricamente: tres arquitecturas comparadas sin alterar la capa de servicio.
- Anadir una arquitectura = registrar una clase. Nada aguas arriba se entera.
- Costo: los objetos de transferencia (`Prediccion`, `ExplicacionLocal`) deben mantenerse.

## Consecuencias negativas
- El puerto es un **contrato estricto** (Ford et al., 2021, cap. 13, p. 365): cualquier cambio
  en su firma invalida a todos los consumidores de forma inmediata.
- Los objetos de transferencia `Prediccion`, `ExplicacionLocal` y `CurvaSensibilidad` pasan a ser
  parte del contrato publico y deben evolucionar con compatibilidad hacia atras.
- La indireccion oculta el costo real de cada implementacion: dos estrategias con la misma
  interfaz pueden diferir en un orden de magnitud de latencia sin que la firma lo declare.

