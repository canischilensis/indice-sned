# ADR-003 — Excluir deliberadamente la capa de MLOps

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
La practica habitual en sistemas de ML incorpora CI/CD, orquestacion de pipelines,
Model Registry gestionado y reentrenamiento continuo. El Indice SNED se calcula
**cada dos anios**.

## Decision
No desplegar infraestructura de orquestacion. Se sustituye por tres mecanismos livianos:
1. Serializacion versionada de artefactos con metadatos (sustituto del Model Registry).
2. Cuadernos de verificacion reproducible, ejecutados en cada publicacion bianual.
3. Control de versiones del codigo sin flujos de CI/CD.

## Consecuencias
- Se evita una fuente de deuda tecnica desproporcionada al ciclo del fenomeno.
- El reentrenamiento es manual y **autorizado por criterio humano**, no automatico.
- Riesgo aceptado: si el ciclo se acortara, esta decision debe revisarse.
