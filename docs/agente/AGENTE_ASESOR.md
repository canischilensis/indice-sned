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
El tablero, el simulador y el reporte de explicabilidad no lo conocen. La cuarta
ventana del cliente si lo conoce, pero hacia el otro lado: es la unica que deja
de funcionar, y lo declara en pantalla en vez de romper la interfaz.

### 3.1 Identidad delegada

El agente **no tiene identidad propia frente al servicio cuando lo usa una
persona**: reenvia el token de quien pregunta. Es la condicion que hace
admisible exponerlo a un navegador. Sin delegacion, CTRL-04 protegeria a la
cuenta con la que el agente se autentica, y un directivo alcanzaria por el
agente establecimientos que la interfaz le niega.

| Punto de entrada | Identidad | Motivo |
|---|---|---|
| Ruta HTTP `/asesor/consulta` | Token del usuario, exigido en la cabecera | Detras hay una persona con jurisdiccion propia |
| Consola `scripts/asesor.py` | Cuenta de servicio de `.env` | No hay usuario detras; es operacion y diagnostico |

Un token delegado vencido **no se renueva solo**: se traduce a `SesionExpirada`,
porque renovar por cuenta propia seria suplantar al usuario. El agente se
construye por peticion y no se memoriza entre llamadas: guardar un agente
compartido significaria compartir tambien la identidad.
`tests/unitarias/q5/test_identidad_delegada.py` fija estas cuatro condiciones.

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
| `gemini` | Operacion | Paquete `google-genai` y `GEMINI_API_KEY` |

Cambiar de proveedor es cambiar dos variables de entorno. El bucle, el catalogo
de herramientas y los cuatro guardarrailes no se tocan: es lo que el puerto
`ProveedorDeModelo` compra.

```bash
AGENTE_PROVEEDOR=gemini
GEMINI_API_KEY=...        # se emite en Google AI Studio
```

### 8.1 Tres asimetrias que el adaptador de Gemini absorbe

El puerto solo sirve si el adaptador se hace cargo de lo que su proveedor tiene
de particular, en vez de filtrarlo hacia el bucle. Gemini tiene tres cosas
particulares, y las tres quedan dentro de `AdaptadorGemini`:

1. **El mensaje de sistema no es un turno.** Viaja en `system_instruction`.
   Mandarlo como turno de la conversacion degrada el seguimiento de la
   instruccion.
2. **El esquema de funciones es un subconjunto de OpenAPI, no JSON Schema.**
   `additionalProperties`, que `simulacion_de_escenario` usa para declarar el
   mapa variable -> valor, no existe alli. El adaptador poda esa clave y traslada
   la restriccion perdida a la descripcion en prosa. Lo que se pierde es la
   validacion de tipo del lado del proveedor; G-01 la impone igual del lado del
   agente, que es donde corresponde: **un guardarrail no puede depender de que
   el proveedor respete el esquema**.
3. **Los tokens de razonamiento se facturan como salida** y llegan en un
   contador aparte, `thoughts_token_count`. El adaptador los suma a la salida.
   Omitirlos haria que la instrumentacion de costo declare menos de lo que el
   proyecto gasta, que es exactamente la clase de cifra que este trabajo no
   puede permitirse.

**El precio depende del modelo, no del proveedor.** Los otros dos adaptadores
fijan la tarifa como constante de clase; el de Gemini la resuelve por modelo
desde una tabla, y cuando el modelo no esta en ella reporta costo cero **y lo
declara** en `describir()` con `precio_declarado: false`. Una tarifa inventada
seria peor que una ausente.

**Dependencias del cuanto.** La consola necesita **httpx y nada mas**: la
configuracion se resuelve con biblioteca estandar, no con pydantic-settings.
No es una preferencia de estilo, es lo que hace cierta la frase "si el cuanto 5
se retira, el sistema sigue operando": tambien al reves, el cuanto 5 arranca sin
la pila del servicio. El servicio HTTP del agente si necesita FastAPI y Pydantic,
que ya vienen en `requirements.txt`.
`tests/arquitectura/test_puntos_de_entrada.py` lo comprueba bloqueando esos
modulos e importando la cadena del CLI.

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
- **Ninguno de los tres adaptadores externos tiene una llamada viva verificada.**
  De Gemini se verifican sin clave la traduccion del esquema, la separacion del
  mensaje de sistema, la traduccion de roles, el conteo de tokens con
  razonamiento incluido, la lectura de la respuesta y los dos modos de fallo de
  construccion —quince pruebas en `test_proveedor_gemini.py`—, y las tres
  declaraciones del catalogo se validan contra el propio SDK. Lo que no esta
  ejercitado es la llamada a la red.
- **La evaluacion corre contra un doble del servicio**, no contra la base
  cargada. Mide que el agente no cite cifras que el servicio no devolvio, no la
  exactitud de esas cifras: eso ya lo verifica la reconstruccion del indice.
- **No hay medicion de costo real por consulta.** La instrumentacion existe y
  esta probada; las cifras se obtendran cuando se enchufe un proveedor.
- **La cuarta ventana no tiene pruebas automatizadas.** El cuanto 4 no tiene
  arnes de pruebas de interfaz: lo unico que la compuerta verifica es que
  `tsc --noEmit` pase. La verificacion de la ventana es manual y esta descrita
  en la seccion 12.

## 12. La cuarta ventana

El agente dejo de ser solo una ruta HTTP y una consola: `q4_cliente` incorpora
**Asesor de gestion** como cuarta ventana, junto al tablero, el simulador y el
reporte de explicabilidad.

| Elemento | Archivo |
|---|---|
| Ventana | `quanta/q4_cliente/src/paginas/Asesor.tsx` |
| Cliente HTTP y tipos | `src/api.ts` (`consultarAsesor`), `src/tipos.ts` |
| Navegacion | `src/App.tsx` (`type Ventana` incorpora `'asesor'`) |
| Direccion del servicio | `VITE_AGENTE_URL`, por defecto `http://127.0.0.1:8010` |

Tres decisiones de esa pantalla, que no son cosmeticas:

1. **La traza es parte de la respuesta, no un detalle plegado.** Cada turno
   muestra que herramienta se invoco, con que resultado y en cuantos
   milisegundos, mas los guardarrailes aplicados y el costo. Un asesor cuya
   cadena de consultas no se puede inspeccionar no es auditable, y este proyecto
   sostiene lo contrario para el resto del sistema.
2. **`VITE_AGENTE_URL` es una direccion distinta de `VITE_API_URL`.** Son dos
   unidades de despliegue, no dos rutas del mismo servicio. Cuando el puerto
   8010 no responde, la ventana dice que el asesor es una unidad aparte y que
   las otras tres siguen operativas, en vez de mostrar un error generico.
3. **El historial no se persiste.** Cambiar de establecimiento o cerrar sesion
   lo descarta. Guardar conversaciones sobre establecimientos identificados
   seria tratamiento de datos que el proyecto no declaro y que ninguna tabla del
   esquema `app` contempla.

Verificacion manual, que es la que hay:

```bash
# tres procesos
uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000
uvicorn q5_agente.app:app    --reload --app-dir quanta --port 8010
cd quanta/q4_cliente && npm run dev        # http://localhost:5173
```

Con el puerto 8010 apagado, la cuarta ventana debe avisar y las otras tres deben
seguir respondiendo. Es la comprobacion de que el cuanto 5 es retirable, hecha
desde la interfaz.

## 13. Como se ejecuta

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

Y la evaluacion, tambien desde la raiz. Con `--respuestas` imprime, caso por
caso, la pregunta, la herramienta que eligio, el resultado de la llamada, los
guardarrailes aplicados y el texto que devolvio. Es la forma de ver el agente
funcionando sin levantar el servicio ni tener credenciales:

```bash
python tests/evaluacion/arnes.py
python tests/evaluacion/arnes.py --respuestas
python tests/evaluacion/arnes.py --json informe_evaluacion.json
```

Con `AGENTE_PROVEEDOR=determinista`, el valor por defecto, no se requiere clave
ni salida a internet. Si el servicio del indice no esta levantado, el agente lo
dice y devuelve codigo de salida distinto de cero: no inventa cifras ni muestra
una traza.

`tests/arquitectura/test_puntos_de_entrada.py` ejecuta estos puntos de entrada
como subprocesos, desde la raiz y con `PYTHONPATH` borrado, para que esta clase
de fallo la detecte la suite y no el usuario.
