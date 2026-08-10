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

### 8.1 Cuatro asimetrias que el adaptador de Gemini absorbe

El puerto solo sirve si el adaptador se hace cargo de lo que su proveedor tiene
de particular, en vez de filtrarlo hacia el bucle. Gemini tiene cuatro cosas
particulares, y las cuatro quedan dentro de `AdaptadorGemini`:

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

4. **La familia de modelos rota, y con ella los parametros admitidos.** Un
   modelo retirado responde 404: se traduce a `ProveedorNoConfigurado`, no a
   `ErrorDelProveedor`, porque el cortacircuitos G-04 existe para proteger de un
   proveedor caido y reintentar contra un modelo que no existe nunca va a
   funcionar. Tratarlo como caida haria que tres consultas mal configuradas
   abrieran el circuito y taparan la causa real. Los parametros de muestreo
   —`temperature`— estan en deprecacion en la linea 3.x: si el modelo los
   rechaza, el adaptador reintenta una vez sin ellos y lo recuerda.

**Elegir el modelo.** `AdaptadorGemini.modelos_disponibles()` pregunta a la
clave cuales puede usar. La familia rota mas rapido que la documentacion: un
modelo con precio publicado puede estar cerrado a claves nuevas, que es
exactamente lo que ocurrio con el defecto inicial de este adaptador,
`gemini-2.5-flash`. El defecto actual es `gemini-3.6-flash`.

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

  > **Superado el 2026-08-10.** El adaptador de Gemini tiene llamada viva
  > verificada contra la API. El texto anterior se conserva a proposito: la
  > limitacion fue real, esta fechada, y saber cuando dejo de serlo vale mas que
  > borrarla. Sigue vigente para Anthropic y OpenAI.

- **La evaluacion corre contra un doble del servicio**, no contra la base
  cargada. Mide que el agente no cite cifras que el servicio no devolvio, no la
  exactitud de esas cifras: eso ya lo verifica la reconstruccion del indice.
- **No hay medicion de costo real por consulta.** La instrumentacion existe y
  esta probada; las cifras se obtendran cuando se enchufe un proveedor.

  > **Superado el 2026-08-10.** Dos consultas reales medidas contra Gemini:
  > USD 0,01248 (4.435 tokens de entrada / 777 de salida) y USD 0,02133 (4.422 /
  > 1.960). El dato que importa para la defensa: la mayoria de esos 1.960 tokens
  > de salida fueron tokens de razonamiento, y el adaptador los suma al costo.
  > Omitirlos habria mostrado la mitad del precio.

- **La latencia que espera un usuario no esta medida.** CP-17 acota en 3.000 ms
  el bucle del agente contra un doble de respuesta fija, y eso es lo unico que
  ese numero significa: el cronometro envuelve la llamada completa, y solo se
  parece al sobrecosto propio del agente porque el doble responde en unidades de
  milisegundos. Hay una medicion puntual del 2026-08-10, misma consulta de
  explicacion por factor: **31 ms contra el doble, 5.906 ms contra el servicio
  levantado sobre parquet**. La diferencia es el calculo de Shapley. Una serie
  medida contra el servicio real, con percentiles, no existe.

  > **Corregido el mismo 2026-08-10.** Atribuir los 5.906 ms al calculo de
  > Shapley es incorrecto. Una consulta posterior contra el mismo servicio, ya
  > tibio, resolvio la misma herramienta en **0 ms**. Los 5.906 fueron **carga en
  > frio de los artefactos de modelo**, no computo. El manual de usuario ya lo
  > declaraba —«los modelos se cargan en el primer uso»— y no se cruzo el dato.
  >
  > El texto anterior se conserva porque la equivocacion ilustra el riesgo que
  > esta misma seccion existe para evitar: **una observacion aislada no
  > distingue un costo permanente de un costo de arranque**. Se declaro una
  > medicion como si fuera una propiedad del sistema.
  >
  > Lo que sigue sin medirse: la latencia en regimen, con percentiles, contra el
  > servicio real. Y el arranque en frio, que es un numero distinto y tambien
  > importa, porque es el que espera el primer usuario del dia.
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

---

## 14. Defectos encontrados por el uso

Los seis que siguen aparecieron el 2026-08-10, al levantar los tres procesos y
lanzar las primeras consultas contra el servicio real. **Ninguno lo encontro la
suite**, que estaba entera en verde. Se registran aqui con su causa, no solo con
su correccion: la causa es lo que se puede evitar la proxima vez.

### D-01 · Una tercera copia de los codigos de factor

El adaptador determinista guardaba su propia tabla de codigos y cuatro de los
seis estaban mal escritos. Pedia `SUPERACR` y el servicio respondia «Factor
desconocido».

Los codigos vivian en **tres** lugares: `COLUMNAS_OBJETIVO` en el cuanto 2, que
es la fuente; `FACTORES` en el catalogo del cuanto 5, duplicado a proposito para
no cruzar la frontera de cuantos; y el mapa de ruteo del determinista, **que
nadie habia registrado**. La prueba `test_codigos_de_factor.py` comparaba los dos
primeros. La tercera copia no la miraba nadie.

El propio catalogo lo advertia: *«el precio de la duplicacion es que puede
desincronizarse, y se desincronizo»*. Tenia razon y se quedo corto.

**Correccion.** La copia se retiro. El determinista lee ahora el `enum` del
esquema de la herramienta, que es el mismo que recibe un modelo de lenguaje. Esa
simetria no es estetica: si la linea base rutea con una tabla propia y el
proveedor externo rutea con el esquema, dejan de ser comparables, y la
comparacion entre ambos es justamente para lo que existe la linea base.

**Verificacion.** `test_codigos_de_factor.py` ejerce ahora el adaptador por su
interfaz publica, una consulta por factor, y exige que ningun codigo emitido
quede fuera del catalogo.

### D-02 · La explicacion devolvia el codigo y no el nombre

`RespuestaExplicacion` traia `factor: "SUPERAR"` y ningun nombre. La prediccion
si lo traia. El resultado: la ventana de explicabilidad y el agente mostraban
`SUPERAR` a un director de establecimiento. El codigo identifica; el nombre es lo
que se lee.

**Correccion.** El esquema declara `nombre`, resuelto contra el catalogo oficial
—la misma fuente que ya usaba la prediccion—. El doble de pruebas replica el
campo, porque un doble mas pobre que el sistema real vuelve a bendecir errores.

### D-03 · CP-11 aprobaba por el mensaje de error

El caso exigia que la respuesta contuviera `superac`. Con el ruteo roto, el
servicio respondia «Factor desconocido: **SUPERAC**R» y esa cadena satisfacia la
exigencia. **El caso llevaba meses en verde por el camino de fallo.**

Al corregir D-01 la llamada empezo a tener exito y el caso se puso rojo por
primera vez de forma honesta. Una prueba que aprueba por un camino de error no
verifica: coincide.

### D-04 · La ausencia de dato se omitia por pequeña

El establecimiento de CP-11 no tiene medicion de SIMCE de segundo medio. El
servicio lo expresa como corresponde —`valor: null`, contribucion `-0,72`— pero
la redaccion solo nombraba las **tres contribuciones de mayor magnitud**, y esa
era la quinta. El agente la descartaba por poco relevante.

Descartar una ausencia por pequeña es exactamente tratarla como cero, que es lo
que este sistema existe para no hacer. La nota de CP-11 lo declaraba desde el
principio —*«la ausencia debe nombrarse, no tratarse como cero»*— y ninguna
asercion lo exigia.

**Correccion.** Toda variable sin valor observado se nombra siempre, entre o no
entre las tres mayores, y se dice explicitamente que la cifra es el efecto de la
falta del dato y no el de un valor bajo. **Recien despues** se agrego la frase
`sin medicion` a CP-11: primero el comportamiento, despues el criterio. Al reves
seria ajustar la prueba a lo que el sistema hace.

### D-05 · El veredicto de la suite dependia de la shell

`pytest -q` pasaba en una terminal y fallaba en otra, sobre el mismo commit. La
causa es la precedencia declarada en `q5_agente.config` —variable del proceso por
encima del archivo `.env`—, correcta en operacion y contaminante en pruebas: una
sesion que hubiera exportado `AGENTE_PROVEEDOR` para levantar el servicio hacia
fallar a una prueba que escribe su propio `.env` temporal y espera leerlo.

Es la segunda vez que el entorno de la maquina se cuela en la suite. La primera
fue mas grave: los subprocesos de `tests/arquitectura/` heredaban el `.env` de la
raiz y salian a internet con la clave de quien ejecutara.

**Correccion.** `tests/unitarias/q5/conftest.py` retira antes de cada prueba toda
variable del cuanto 5. La lista **no se escribe a mano**: se deriva de los campos
de `ConfiguracionDelAgente`, de modo que un campo nuevo queda protegido sin que
nadie tenga que acordarse.

### D-06 · El proveedor externo respondia en Markdown, y con punto decimal

La primera consulta real contra Gemini devolvio Markdown completo: negritas,
encabezados `###`, reglas horizontales, listas anidadas y cursivas. La ventana
pinta el texto sin interpretar marcado, de modo que el directivo habria leido los
asteriscos. El adaptador determinista no lo hacia, y por eso toda la verificacion
previa —hecha contra el determinista— no podia verlo.

En la misma respuesta aparecio un segundo defecto: los decimales con punto
—`59.2`, `16.58`—, mientras el determinista escribia `59,20` y `16,58`. **El mismo
sistema mostraba el numero de dos formas segun el proveedor**, y una de las dos no
es la convencion chilena.

**Correccion en dos capas, y las dos hacen falta.**

La primera es pedirlo: el mensaje de sistema declara ahora que la respuesta es
prosa plana y que los decimales van con coma. La segunda es no depender de eso.
`q5_agente/redaccion.py` normaliza el texto final en el bucle, para cualquier
proveedor presente o futuro. **Una instruccion a un modelo es una peticion, no una
garantia**, y es el mismo criterio de G-02: no se le pide al modelo que cite bien,
se verifica que lo haya hecho.

La normalizacion se aplica **antes** de evaluar la politica de salida. Validar una
version del texto y entregar otra dejaria un hueco por donde no mira nadie.

**Lo que no se hizo, a proposito.** No se renderiza Markdown en el cliente.
Convertir la salida de un modelo de lenguaje en marcado que el navegador ejecuta
es una puerta que este sistema no necesita abrir por un problema de negritas.

**Frontera del criterio.** Hacia el usuario, coma; internamente, punto. Los datos
viajan y se comparan en punto —es lo que devuelve el servicio y lo que lee el
guardarrail— y solo el texto que se muestra usa la convencion local.

**Limitacion declarada.** Solo se convierten decimales de una o dos cifras. Tres
digitos tras un punto son indistinguibles de un grupo de millar en castellano
—`4.435` son cuatro mil— y equivocarse en ese sentido corrompe una cantidad. Un
numero con tres o mas decimales conserva el punto.

**Verificacion.** `tests/unitarias/q5/test_redaccion.py`, sobre una captura
literal de la respuesta de Gemini. La consulta se repitio contra el proveedor real
despues de corregir: prosa sin marcas, diecisiete cifras con coma y G-02 en verde,
que era el riesgo real —cambiar el separador podia romper la extraccion de
magnitudes del guardarrail—.

### Lo que los seis tienen en comun

Cinco de los seis son el mismo error de fondo: **una copia de la verdad que nadie
verificaba, o un banco de pruebas mas pobre que el sistema**. El codigo de factor
duplicado tres veces, el doble mas pobre que el servicio, el criterio de prueba
desalineado de su intencion declarada, el entorno del operador filtrandose en el
veredicto, y toda la evaluacion hecha contra un proveedor que no se comporta como
el proveedor real.

El sexto agrega una leccion propia: **lo que se le pide a un modelo hay que
verificarlo aparte**. Vale para las cifras y vale para el formato.

La leccion quedo escrita como regla exigible en `PLAN_CALIDAD.md`, seccion 9.1.

---

## 15. Historial de modificaciones

Nada se elimina de este documento. Lo que deja de ser cierto se marca como
superado y conserva su texto: saber cuando una limitacion dejo de serlo vale mas
que borrarla.

| Fecha | Seccion | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-10 | 11 | Se marca como superada la limitacion «ningun adaptador externo tiene llamada viva verificada» | Gemini tiene llamada viva verificada. Sigue vigente para Anthropic y OpenAI |
| 2026-08-10 | 11 | Se marca como superada la limitacion «no hay medicion de costo real por consulta» | Dos consultas medidas: USD 0,01248 y USD 0,02133, con tokens de razonamiento incluidos en el costo |
| 2026-08-10 | 14 | Seccion nueva: cinco defectos encontrados por el uso, con causa y correccion | Ninguno lo detecto la suite; el registro de la causa es lo que evita la repeticion |
| 2026-08-10 | 15 | Seccion nueva: este historial | Se adopta la convencion de conservar el registro de modificaciones en todos los documentos |
| 2026-08-10 | 11 | Se declara que la latencia percibida por el usuario no esta medida, con la medicion puntual 31 ms / 5.906 ms | CP-17 se llamaba «latencia propia del agente» y el arnes decia «excluida la del servicio». Ninguna de las dos etiquetas era exacta: el cronometro envuelve la llamada completa |
| 2026-08-10 | 11 | Se corrige la atribucion de los 5.906 ms: fue arranque en frio, no calculo. La afirmacion anterior se conserva marcada | Una consulta posterior contra el mismo servicio ya tibio resolvio la misma herramienta en 0 ms. Se habia elevado una observacion aislada a propiedad del sistema |
| 2026-08-10 | 14 | Se agrega D-06: Markdown y punto decimal en el proveedor externo | La primera consulta real contra Gemini devolvio marcado que la ventana pinta literal. La verificacion previa, hecha contra el determinista, no podia verlo |
