# ADR-001 — Organizar el sistema en cuatro cuantos de arquitectura

**Estado:** aceptada · **Fecha:** 2026-08-01

## Contexto
El proyecto mezcla un pipeline analitico batch de periodicidad bianual con una aplicacion
web interactiva. Un monolito unico haria que cualquier cambio en el motor obligara a
redesplegar la interfaz, y viceversa.

## Decision
Separar el sistema en cuatro cuantos con despliegue independiente: ingesta, modelamiento,
servicio y cliente. Cada uno reside en `quanta/` y solo cruza fronteras por contratos explicitos.

## Alternativas descartadas
- **Monolito unico sin fronteras internas.** Descartado: cualquier cambio en el motor obligaria
  a redesplegar la interfaz, y la prohibicion de importar librerias de ML dejaria de ser
  verificable.
- **Microservicios distribuidos, un servicio por cuanto.** Descartado por baja concurrencia y
  ciclo bianual: el costo de coordinacion, transacciones distribuidas y observabilidad excede
  el beneficio en un sistema consultado por equipos directivos, no por trafico masivo.
- **Separacion por capas tecnicas (presentacion, negocio, datos) en lugar de por cuantos.**
  Descartado porque agrupa por tecnologia y no por dimension de cambio: el motor predictivo y
  el control de acceso cambian por razones distintas y a ritmos distintos.

## Consecuencias
- El pipeline puede correr en un notebook o en un servidor batch sin tocar el servicio.
- El cuanto 3 no puede importar librerias de ML: `scripts/verificar_arquitectura.py` lo verifica.
- Costo: mas archivos, mas indireccion y latencia de red entre cliente y servicio.

## Consecuencias negativas
- **Los cuatro cuantos son logicos; las unidades de despliegue son tres.** Q2 y Q3 comparten
  espacio de proceso, de modo que bajo los tres criterios de Ford et al. (2021, cap. 2,
  pp. 29-30) constituyen un unico cuanto fisico. La independencia de despliegue que este
  registro afirmaba es real para Q1 y Q4, no para Q2 y Q3.
- La conascencia estatica entre Q3 y Q2 es de nombre y tipo: un cambio en la firma del puerto
  obliga a modificar ambos a la vez.
- Mas archivos, mas indireccion y un grafo de dependencias que hay que mantener verificado.

## Riesgo de erosion
Con un ciclo bianual, un equipo futuro puede rediscutir esta particion sin conocer las razones
que la produjeron: es el anti-patron del dia de la marmota (Richards y Ford, 2020, cap. 19,
p. 282). Las alternativas descartadas se documentan aqui precisamente para que esa discusion no
tenga que repetirse desde cero.

