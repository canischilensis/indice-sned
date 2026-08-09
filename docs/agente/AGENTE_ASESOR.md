# Cuanto 5 · Agente asesor de gestion

Identificador del documento: **AG-SNED-01**

Traduce y prioriza lo que el sistema ya calcula. No calcula nada.

---

## 1. Por que existe

El sistema construido cierra la brecha entre el dato disperso y la informacion
correcta, pero no la que va de la informacion a la decision. Un equipo directivo
que abre el reporte de explicabilidad encuentra que la medicion de matematica
aporta 4,21 puntos y que los procesos con sancion restan 1,20: cifras exactas y
auditables que no responden la pregunta operativa, que es que mover primero,
cuanto rinde moverlo y que no vale la pena tocar.

## 2. Principio rector

**El agente orquesta y traduce; el motor predictivo calcula; el equipo directivo
decide.** El modelo de lenguaje no computa el indice ni pondera factores. Esa
formula vive en el cuanto 2 y esta verificada contra el calculo oficial con una
discrepancia maxima de 0,0006 sobre 44.679 establecimientos. Duplicarla en un
componente probabilistico seria cambiar una propiedad demostrada por una
plausible.

## 3. Ubicacion arquitectonica

El agente entra como quinto cuanto detras del puerto `AsesorDeGestion`, del
mismo modo en que `RepositorioEstablecimientos` gobierna sus dos adaptadores.

```
q5_agente  ->  compartido        (unica dependencia interna permitida)
q5_agente  ->  HTTP -> servicio  (como cualquier usuario, sometido a CTRL-04)
```

No importa `q3_servicio` ni `q2_modelamiento`. La compuerta de arquitectura lo
verifica en cada integracion, y existe una prueba negativa que introduce la
importacion prohibida y comprueba que el script falla.

Consecuencia practica: **si el cuanto 5 se retira, el sistema sigue operando**.
El tablero, el simulador y el reporte de explicabilidad no lo conocen.

## 4. Las tres herramientas

Cada una envuelve rutas que ya existen y estan probadas.

| Herramienta | Rutas que envuelve | Responde |
|---|---|---|
| `diagnostico_de_establecimiento` | `GET /prediccion/{rbd}`, `GET /prediccion/{rbd}/alertas`, `GET /establecimientos/{rbd}/ranking` | Que situacion tiene el establecimiento |
| `explicacion_por_factor` | `GET /xai/{rbd}/shapley` | Por que obtuvo ese resultado |
| `simulacion_de_escenario` | `POST /prediccion/{rbd}/escenario` | Cuanto rinde mover una palanca |

La posicion intragrupo es complementaria dentro del diagnostico: si la vista de
ordenamiento no esta disponible, el diagnostico se entrega igual y la ausencia
se declara, en lugar de omitirse en silencio.

## 5. Por que no hay recuperacion aumentada

El dato de este sistema ya esta estructurado en una base relacional normalizada
y expuesto por una interfaz tipada. Fragmentar esos registros para recuperarlos
por similitud semantica seria incompatible con la integridad relacional que el
proyecto construyo, e introduciria imprecision justamente donde la consulta
directa es deterministica.

| Criterio | Consulta directa por herramienta | Recuperacion semantica |
|---|---|---|
| Precision del dato | Deterministica: el registro exacto | Probabilistica: depende del ordenamiento |
| Integridad relacional | Garantizada por el esquema | Se rompe al fragmentar la fila |
| Latencia | Una llamada | Vectorizacion mas busqueda mas llamada |
| Verificabilidad | La cifra tiene origen | El origen es un fragmento de texto |

## 6. Los guardarrailes

Cuatro barreras. Las tres primeras son objetos `Especificacion`, el mismo puerto
que gobierna la cuarentena de la ingesta y las reglas de alerta del servicio.

| Codigo | Que impide | Donde vive | Como se comprueba |
|---|---|---|---|
| **G-01** | Inyeccion por parametro y movimiento del objetivo del modelo | `SanitizadorDeParametros` | 7 pruebas unitarias; CP-18 |
| **G-02** | Cifras que ninguna herramienta devolvio | `CifrasFundadasEnHerramientas` | 5 pruebas; los 20 casos, agregado |
| **G-03** | Promesas de obtencion del beneficio | `SinPromesasDeRetorno` | 4 pruebas; CP-07 |
| **G-04** | Responder cuando el proveedor esta caido | Bucle y cortacircuitos | 4 pruebas de decorador |

El gateway traduce ademas los fallos de **transporte** —servicio apagado, tiempo
agotado— a `ServicioNoDisponible`, de modo que un puerto cerrado se comunica
como una condicion del dominio y no como una traza de httpx.

Dos precisiones sobre G-02, porque su alcance importa mas que su existencia:

1. Solo evalua **magnitudes**: decimales, porcentajes y enteros de dos digitos o
   mas. Los enteros de un digito quedan fuera a proposito, para no rechazar
   enumeraciones como "los seis factores". Es una limitacion declarada.
2. Las cifras del **propio pedido** —el RBD, el bienio, los valores que el
   directivo fijo en el escenario— cuentan como respaldadas. No son invencion
   del modelo, y el agente debe poder repetirlas al explicar un error.
3. Las cifras que aparecen en un **mensaje del sistema** —el RBD dentro de un
   403, el puerto dentro de un error de conexion, el rango dentro de un 422—
   viajan en un conjunto aparte, `cifras_de_diagnostico`. Se admiten al validar,
   pero no se presentan como evidencia de dato. La respuesta transporta ambos
   conjuntos para que la auditoria vea con cual exacto se evaluo G-02.

G-01 incorpora ademas la regla que CTRL-02 impone al modelamiento: el indice, los
seis factores y la agrupacion de comparacion **no pueden entrar como parametro**.
El objetivo no es una palanca.

## 7. Orquestacion

Bucle de ejecucion simple: observa, decide una herramienta, la ejecuta, observa
el resultado y responde, con un maximo de pasos configurable. Escalar a
planificacion explicita solo se justificaria con evidencia de que la complejidad
lo exige, y esa evidencia no existe todavia.

## 8. Proveedores

| Adaptador | Uso previsto | Requiere |
|---|---|---|
| `determinista` | Pruebas, evaluacion e integracion continua | Nada |
| `anthropic` | Operacion | Paquete `anthropic` y `ANTHROPIC_API_KEY` |
| `openai` | Operacion | Paquete `openai` y `OPENAI_API_KEY` |

**El adaptador determinista no es un modelo de lenguaje.** Es la implementacion
de referencia del puerto: rutea por pertinencia y redacta por plantilla sobre
los datos que la herramienta devolvio. Existe por tres razones. Permite que la
suite corra en cualquier maquina sin clave y sin red. Fija el comportamiento
esperado del bucle. Y da una linea base contra la cual medir a un proveedor
real: si el modelo externo rutea peor que un puñado de reglas, el modelo no
aporta.

## 9. Instrumentacion de costo

El decorador `ProveedorInstrumentado` mide tokens de entrada, tokens de salida,
costo en dolares y latencia **desde la primera llamada**, no despues. El costo
por consulta viaja en la respuesta de la ruta del agente y en la salida de la
consola con `--trazas`.

## 10. Evaluacion: los veinte casos criticos

`tests/evaluacion/` contiene la matriz completa. Se ejecuta como parte de la
suite y tambien de forma independiente:

```bash
python tests/evaluacion/arnes.py
python tests/evaluacion/arnes.py --json informe_evaluacion.json
```

Mide cinco cosas: ruteo de herramienta, fundamentacion de cifras, ausencia de
promesas, resiliencia ante 403, 404, 422 y 503, y latencia propia del agente.

**Tres casos de la propuesta original se reformularon**, y la diferencia se
declara para que no se lea como omision:

| Caso | Propuesta original | Reformulacion | Motivo |
|---|---|---|---|
| CP-09 | Comparacion entre dos distritos | Comparacion entre dos RBD de la misma jurisdiccion | En Chile los establecimientos se agrupan en comunas y Grupos Homogeneos; no hay distritos escolares |
| CP-13 | Registros previos a 1990 | Periodo anterior a la ventana 2016-2025 | Es el limite verificable del proyecto |
| CP-20 | Impacto de las becas en el indice | Variable que el indice no observa, sobre un RBD con artefacto ausente | Las becas no son insumo del indice |

## 11. Lo que no esta medido

Se declara, porque la politica de calidad del proyecto exige que lo que no se
cumple se declare:

- **La calidad de redaccion de un proveedor real no esta medida.** Los veinte
  casos se ejecutan contra el adaptador determinista. Lo que esta verificado es
  el bucle, el ruteo, los guardarrailes y la resiliencia, no la prosa de un
  modelo externo.
- **La evaluacion corre contra un doble del servicio**, no contra la base
  cargada. Mide que el agente no cite cifras que el servicio no devolvio, no la
  exactitud de esas cifras: eso ya lo verifica la reconstruccion del indice.
- **No hay medicion de costo real por consulta.** La instrumentacion existe y
  esta probada; las cifras se obtendran cuando se enchufe un proveedor.
- **No hay cuarta ventana.** La interfaz del agente es una ruta HTTP y una
  consola. Integrarla al prototipo es alcance nuevo, sujeto al procedimiento de
  control de cambios.

## 12. Como se ejecuta

Los cuantos viven en `quanta/`, que no esta en la ruta de Python salvo que algo
la ponga: pytest lo hace por el `pythonpath` de `pyproject.toml` y uvicorn por
`--app-dir quanta`. Por eso la consola se invoca con el lanzador de `scripts/`,
que resuelve la ruta el mismo.

```bash
# 1. El servicio del indice, en un proceso
uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000

# 2. El agente, en otro proceso (unidad de despliegue propia)
uvicorn q5_agente.app:app --reload --app-dir quanta --port 8010

# 3. O directamente por consola, desde la raiz del repositorio
python scripts/asesor.py --rbd 25520 --trazas "por que se nos cae la superacion"
```

Equivalente sin el lanzador, si prefiere la variable de entorno:

```powershell
$env:PYTHONPATH = "quanta"
python -m q5_agente.cli --rbd 25520 --trazas "por que se nos cae la superacion"
```

Y la evaluacion, tambien desde la raiz:

```bash
python tests/evaluacion/arnes.py
python tests/evaluacion/arnes.py --json informe_evaluacion.json
```

Con `AGENTE_PROVEEDOR=determinista`, el valor por defecto, no se requiere clave
ni salida a internet. Si el servicio del indice no esta levantado, el agente lo
dice y devuelve codigo de salida distinto de cero: no inventa cifras ni muestra
una traza.

`tests/arquitectura/test_puntos_de_entrada.py` ejecuta estos puntos de entrada
como subprocesos, desde la raiz y con `PYTHONPATH` borrado, para que esta clase
de fallo la detecte la suite y no el usuario.
