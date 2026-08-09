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

## Alternativas descartadas
- **Plataforma completa de MLOps** con orquestacion de pipelines, registro gestionado y
  reentrenamiento continuo. Descartada: el fenomeno se calcula cada dos anios y la
  infraestructura seria deuda tecnica desproporcionada a su ciclo.
- **Registro de modelos gestionado por servicio externo, sin el resto de la plataforma.**
  Descartado por introducir una dependencia de red y un costo recurrente para resolver un
  problema que un directorio versionado con metadatos resuelve.
- **Reentrenamiento programado por calendario.** Descartado: reentrenar sin senal de deriva
  introduce variacion sin ganancia. La verificacion de deriva es la que debe disparar el
  reentrenamiento, no el calendario.

## Consecuencias
- Se evita una fuente de deuda tecnica desproporcionada al ciclo del fenomeno.
- El reentrenamiento es manual y **autorizado por criterio humano**, no automatico.
- Riesgo aceptado: si el ciclo se acortara, esta decision debe revisarse.

## Consecuencias negativas
- **No existe deteccion automatica de deriva.** La verificacion es manual y depende de que
  alguien la ejecute en el ciclo correspondiente.
- El reentrenamiento depende de memoria institucional. Con dos anios entre ejecuciones, esa
  memoria se pierde: es la razon por la que los procedimientos operativos se documentaron.
- Si el ciclo del fenomeno se acortara, la decision no se degrada de forma progresiva sino que
  deja de ser valida de golpe.
- Los artefactos quedan sin verificacion automatica de compatibilidad de version, brecha que ya
  se materializo: fueron serializados con una version de la libreria distinta de la del entorno
  de servicio.

