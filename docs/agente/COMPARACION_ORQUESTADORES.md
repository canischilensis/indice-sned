# Comparación medida entre dos orquestadores

Identificador del documento: **CO-SNED-01**
Fecha de la medición: **10 de agosto de 2026**

Un bucle de ejecución escrito a mano contra el agente ReAct que LangGraph trae de
fábrica, detrás del mismo puerto y sobre los mismos veinte casos críticos.

---

## 1. Por qué existe esta medición

El puerto `AsesorDeGestion` tenía **un solo adaptador**. Un puerto con un solo
adaptador es una promesa sin cobrar: se declara que la implementación es
sustituible y nadie lo ha comprobado. `RepositorioEstablecimientos` sí lo tenía
comprobado —Parquet y PostgreSQL, con pruebas de paridad—, y esa diferencia era
una deuda de la arquitectura, no un detalle.

El segundo adaptador salda esa deuda y, de paso, responde una pregunta que la
literatura de agentes suele contestar por adhesión: **qué aporta un framework de
orquestación sobre un bucle propio, y qué cuesta.**

**Los veinte casos críticos no se modificaron.** Ni uno. Que sirvan para evaluar
los dos adaptadores sin tocarse es, por sí solo, el resultado de arquitectura:
están escritos contra el puerto y no contra su implementación.

## 2. Diseño experimental

**Una variable en movimiento.** Se mueve el orquestador y nada más. Todo lo demás
es idéntico y compartido, no reimplementado:

| Componente | Compartido |
|---|---|
| Doble del servicio | `ServicioFalso`, mismas cargas fijas |
| Catálogo de herramientas | el del cuanto 5, con su sanitizador |
| Proveedor de modelo | `AdaptadorDeterminista`, mismos disparadores |
| Política de salida | `PoliticaDeSalida` con G-01, G-02 y G-03 |
| Normalización del texto | `a_prosa_plana` |
| Cifras del contexto | `cifras_del_contexto`, en el contrato |

La comparación entre **proveedores** —determinista contra Gemini contra un modelo
local— es un experimento distinto, con su propia tabla. Cruzar ambas produciría
ocho celdas que se leen como fuerza bruta en lugar de como diseño.

**El proveedor es el determinista a propósito.** Sin red y sin credencial, de modo
que ninguna diferencia observada pueda venir de dos respuestas distintas del mismo
modelo. Lo que se mide es la orquestación, no la suerte.

**Cómo se sostiene la equivalencia del proveedor.** `create_react_agent` espera un
`BaseChatModel` de LangChain. Lo directo habría sido pasarle el cliente de
LangChain para Gemini, y entonces se moverían dos variables a la vez —orquestador
y cliente—. En su lugar, `_ModeloDesdeProveedor` presenta el puerto
`ProveedorDeModelo` con la interfaz que LangGraph espera. Cien líneas de
traducción que compran que la comparación signifique lo que dice.

## 3. Resultados

Veinte casos, proveedor determinista, `AGENTE_MAX_PASOS=3`.

| Métrica | bucle propio | LangGraph ReAct |
|---|---:|---:|
| Casos aprobados | 20/20 | 20/20 |
| Ruteo de herramienta correcto | 20/20 | 20/20 |
| Cifras fundadas · G-02 | 20/20 | 20/20 |
| Sin promesas de retorno · G-03 | 20/20 | 20/20 |
| Rechazos de política correctos | 7 | 7 |
| Resiliencia 403 / 404 / 422 / 503 | 2 | 2 |
| Llamadas a herramienta | 15 | 15 |
| Llamadas al modelo | 35 | 35 |
| Tokens de entrada | 25.617 | 25.617 |
| Tokens de salida | 2.845 | 2.845 |
| Costo USD | 0,0 | 0,0 |
| Latencia p50 | 0 ms | 0 ms |
| **Latencia p95** | **0 ms** | **16 ms** |
| **Dependencias transitivas** | **1** | **15** |

### 3.1 Los tokens idénticos son parte del resultado

25.617 y 2.845 en ambas columnas, hasta la unidad. **No es una coincidencia: es la
verificación de que el experimento aisló una sola variable.** Si el envoltorio del
modelo hubiera alterado el diálogo —un mensaje de sistema distinto, un rol mal
traducido, una herramienta declarada de otra forma— ese número se habría movido.

Una comparación cuyo control no se puede exhibir es una opinión con tabla.

### 3.2 La latencia depende de la máquina

p95 de **16 ms** en Windows 11 y **10 ms** en un Linux contenerizado, sobre el mismo
commit. El invariante no es la cifra sino el orden de magnitud: LangGraph agrega
una decena de milisegundos de orquestación por consulta, y el bucle propio no es
medible a esta resolución.

Ninguno de los dos números representa lo que espera un usuario: el doble responde
con cargas fijas. Ver la sección 11 de `AGENTE_ASESOR.md`.

## 4. Lectura

**Para esta carga, el framework no compra ninguna diferencia medible de calidad.**
Mismo ruteo, mismos guardarraíles satisfechos, mismas llamadas, mismos tokens. Y
cuesta catorce dependencias transitivas más y una decena de milisegundos.

Eso **no** dice que LangGraph sobre. Dice **a partir de dónde empieza a pagar lo
que cuesta**, y ese umbral se puede nombrar: el agente tiene presupuesto de tres
pasos y una herramienta por consulta. Los puntos de control para reanudar una
ejecución interrumpida, la transmisión por partes, las aristas condicionales y el
estado persistido —que es lo que el framework realmente vende— no se usan porque
este problema no los necesita.

La conclusión defendible no es «framework bueno» ni «framework innecesario». Es
que **un framework de orquestación se elige por la complejidad del grafo, no por
la del problema**, y aquí el grafo tiene dos nodos.

## 5. Lo que esta medición no dice

- **No mide calidad de redacción.** El proveedor determinista escribe por
  plantilla. Comparar prosa exige un proveedor real y es otro experimento.
- **No mide comportamiento bajo un modelo de lenguaje real.** Un modelo externo
  podría rutear distinto bajo cada orquestador; con el determinista, por
  construcción, no.
- **No mide lo que el framework aporta fuera de este alcance.** Un agente con
  diez herramientas, ramas condicionales o ejecución reanudable es otro problema.
- **No mide desarrollo.** Cuánto cuesta escribir, leer y mantener cada uno es una
  dimensión real y aquí no está cuantificada.

## 6. Hallazgo colateral: la rotación del ecosistema

`langgraph.prebuilt.create_react_agent` **está obsoleto desde LangGraph V1.0** y
desaparece en V2.0: se mudó al paquete `langchain` como `langchain.agents.create_agent`.

La medición se hizo con la función que LangGraph 1.2.10 sigue publicando, porque
la pregunta es qué entrega LangGraph. Seguir la migración cuesta **un paquete
adicional** —`langchain`, que elevaría la cuenta de dependencias de 15 a 16— o
construir el grafo a mano con `StateGraph`, que es API estable pero deja de ser
«lo que el framework trae de fábrica».

Es un dato de decisión, no una queja: adoptar un framework incorpora también su
ritmo de cambio, y ese costo no aparece en ninguna comparación de calidad.

## 7. Cómo reproducirla

```bash
pip install langgraph
python tests/evaluacion/comparar.py
python tests/evaluacion/comparar.py --json comparacion.json
```

El arnés admite además evaluar un orquestador por separado:

```bash
python tests/evaluacion/arnes.py --orquestador langgraph_react --respuestas
```

Y en operación se elige por configuración:

```bash
AGENTE_ORQUESTADOR=bucle_simple      # sin mas dependencia que httpx
AGENTE_ORQUESTADOR=langgraph_react   # requiere langgraph instalado
```

`langgraph` es **dependencia opcional**. El módulo se importa de forma perezosa
desde la fábrica, igual que los SDK de los proveedores externos, de modo que la
consola sigue arrancando con `httpx` como única dependencia y la compuerta de
arquitectura pasa sin excepciones. Las pruebas del adaptador se omiten enteras si
el paquete no está instalado.

## 8. Historial de modificaciones

| Fecha | Sección | Cambio | Motivo |
|---|---|---|---|
| 2026-08-10 | — | Documento nuevo | Primera medición entre los dos adaptadores del puerto `AsesorDeGestion` |
