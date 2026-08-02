# ADR-001 — Organizar el sistema en cuatro cuantos de arquitectura

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
El proyecto mezcla un pipeline analitico batch de periodicidad bianual con una aplicacion
web interactiva. Un monolito unico haria que cualquier cambio en el motor obligara a
redesplegar la interfaz, y viceversa.

## Decision
Separar el sistema en cuatro cuantos con despliegue independiente: ingesta, modelamiento,
servicio y cliente. Cada uno reside en `quanta/` y solo cruza fronteras por contratos explicitos.

## Consecuencias
- El pipeline puede correr en un notebook o en un servidor batch sin tocar el servicio.
- El cuanto 3 no puede importar librerias de ML: `scripts/verificar_arquitectura.py` lo verifica.
- Costo: mas archivos, mas indireccion y latencia de red entre cliente y servicio.
