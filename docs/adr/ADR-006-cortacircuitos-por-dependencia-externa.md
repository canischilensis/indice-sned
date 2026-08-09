# ADR-006 · Reevaluacion del patron Cortacircuitos por la incorporacion del cuanto 5

- **Estado:** aceptada
- **Fecha:** agosto de 2026
- **Reemplaza parcialmente:** la ficha de descarte de Circuit Breaker en `docs/PATRONES_DE_DISENO.md`, seccion 3

## Contexto

`docs/PATRONES_DE_DISENO.md` descarto el patron Cortacircuitos con un argumento
explicito y, en su momento, correcto:

> No hay llamadas a servicios externos en tiempo de ejecucion. La ingesta es
> estatica y bianual.

Ese argumento sostuvo el descarte mientras el sistema tuvo exactamente tres
dependencias en ejecucion, todas locales: el registro de artefactos en disco, la
base PostgreSQL en red privada y los archivos columnares. Ninguna de ellas es un
tercero, ninguna cobra por llamada y ninguna se degrada de forma parcial.

El cuanto 5 rompe esa premisa. El agente asesor invoca a un proveedor de modelos
de lenguaje por red publica. Esa llamada puede fallar, puede tardar, puede
limitarse por cuota y puede degradarse sin devolver error. Es, por primera vez
en el proyecto, una dependencia externa en tiempo de ejecucion.

## Decision

Se implementa el patron Cortacircuitos **unicamente sobre el puerto
ProveedorDeModelo**, en `quanta/q5_agente/decoradores.py`, como decorador del
mismo puerto que envuelve.

Tres estados, con los valores por defecto declarados en configuracion:

| Estado | Comportamiento | Transicion |
|---|---|---|
| Cerrado | Deja pasar toda llamada | Abre tras 3 fallos consecutivos |
| Abierto | Corta sin intentar la llamada | Pasa a semiabierto tras 30 s |
| Semiabierto | Deja pasar una sola llamada de sondeo | Cierra si tiene exito; reabre si falla |

El cortacircuitos **no** se extiende al puerto RepositorioEstablecimientos ni al
registro de artefactos. Ahi el argumento original sigue vigente: son
dependencias locales, y un cortacircuitos sobre ellas seria ceremonia sin riesgo
que mitigar.

## Consecuencias

**Positivas.** Un proveedor caido deja de propagar latencia al equipo directivo:
el agente responde de inmediato que no puede redactar, y los datos siguen
disponibles en el tablero y en el reporte de explicabilidad, que no dependen del
cuanto 5. El estado del circuito es observable en la ruta de salud del agente.

**Negativas.** El cortacircuitos introduce estado mutable en un componente que
hasta ahora era sin estado, y ese estado es por proceso: dos instancias del
agente abren y cierran de forma independiente. Con una sola instancia el efecto
es nulo; si alguna vez se replica el cuanto 5, habra que decidir si el estado se
comparte o se acepta la divergencia. Se declara ahora para no descubrirlo
despues.

**Sobre la evaluacion.** El comportamiento de los tres estados se verifica en
`tests/unitarias/q5/test_decoradores_y_bucle.py` con un reloj falso, de modo que
la prueba no depende del paso real del tiempo.

## Alternativas descartadas

**Reintento con espera exponencial, sin cortacircuitos.** Resuelve el fallo
transitorio pero empeora el fallo sostenido: multiplica las llamadas contra un
proveedor que ya esta caido y multiplica el costo. Se puede añadir mas adelante
*dentro* del estado cerrado, sin sustituir esta decision.

**Mamparo por tipo de consulta.** Aislar el presupuesto de llamadas por tipo de
consulta tendria sentido con varios flujos concurrentes en competencia. El
cuanto 5 atiende a equipos directivos, con concurrencia baja y un solo flujo:
seria una particion sin nada que particionar.

**No mitigar y declarar el riesgo.** Es lo que hacia el proyecto hasta ahora, y
era coherente mientras no existiera la dependencia. Con el agente, dejarlo sin
mitigar traslada al usuario final una espera que el sistema puede evitar.
