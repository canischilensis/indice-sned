# Diagramas del proyecto

Los diagramas de arquitectura se derivaron **del código real**, no de un diseño ideal. Donde el
código no coincidía con lo esperado, se documentó lo que hay.

Los dos diagramas de datos (`00_*`) son los originales de ERDPlus y draw.io. Los de arquitectura
(`01_*` a `06_*`) tienen fuente en Mermaid (`.mmd`) más exportación a PNG para pegar en el
documento de tesis.

> **Nota sobre el origen del modelo físico.** `00_modelo_fisico_bd.drawio.png` es la exportación
> a imagen del diagrama de draw.io. El archivo fuente `.drawio` **no está versionado**: para
> poder editarlo desde el repositorio hay que exportarlo desde draw.io y guardarlo junto al PNG.

Documentos relacionados fuera de esta carpeta: `docs/Anexo_mapeo_conceptual_fisico.docx`
(la derivación conceptual → físico) y `db/esquema_sned_canonico.sql` (el DDL de referencia
del que se partió `db/esquemas/`).

| # | Archivo | Qué muestra | Origen |
|---|---------|-------------|--------|
| 0 | `00_modelo_entidad_relacion.png` | Modelo conceptual: 12 entidades, especialización, atributos derivados | ERDPlus |
| 0 | `00_modelo_fisico_bd.drawio.png` | Modelo físico del dominio `core` + `hechos` | draw.io |
| 1 | `01_hexagonal` | Los cuatro puertos con sus adaptadores concretos | Mermaid |
| 2 | `02_patrones` | Los doce patrones aplicados, vista completa | Mermaid |
| 2a | `02a_patrones_motor` | Patrones del motor predictivo Q2: Strategy, Decorator, Factory Method, Registry, Virtual Proxy y Builder | Mermaid, derivado de `02_patrones` |
| 2b | `02b_patrones_servicio` | Patrones de ingesta y servicio Q1 y Q3: Specification, Template Method, Repository, Adapter, Abstract Factory y Facade | Mermaid, derivado de `02_patrones` |
| 3 | `03_secuencia_prediccion` | De la petición HTTP a la respuesta, pasando por los seis modelos | Mermaid |
| 4 | `04_secuencia_simulacion` | El what-if completo y las 54 inferencias que explican los 4,6 s | Mermaid |
| 5 | `05_secuencia_shap` | De la petición a la atribución por variable, y de dónde sale el vector | Mermaid |
| 6 | `06_contexto` | Las cuatro etapas del ecosistema y los flujos donde opera cada control CTRL-01 a CTRL-05 | Mermaid |
| 6 | `06_despliegue` | Las tres unidades de despliegue y los cuatro cuantos lógicos | Mermaid |

## Regenerar los PNG

```bash
npm install -g @mermaid-js/mermaid-cli
cd docs/diagramas
for f in *.mmd; do mmdc -i "$f" -o "${f%.mmd}.png" -b white -s 3; done
```

## Los cuatro puertos, verificados en el código

Son exactamente las cuatro clases que heredan de `ABC` en `quanta/`:

| Puerto | Archivo | Adaptadores |
|--------|---------|-------------|
| `Especificacion[T]` | `compartido/especificacion.py` | 5 reglas de cuarentena, 4 reglas de alerta, 3 combinadores |
| `IngestorDeFuente` | `q1_ingesta/ingestor.py` | `IngestorExcel`, `IngestorCsv`, `IngestorCsvUtf8` |
| `EstrategiaPredictiva` | `q2_modelamiento/contrato.py` | `EstrategiaDesagregada`, `EstrategiaGlobal`, 2 decoradores |
| `RepositorioEstablecimientos` | `q3_servicio/repositorios/contrato.py` | `RepositorioParquet`, `RepositorioPostgres` |

`RegistroDeModelos` **no** es un puerto: es una clase concreta. Aparece en el diagrama de
patrones como Registry, no en el hexagonal.

## Tres cosas que el código dice y un diseño ideal no diría

**El orden de las columnas lo manda el artefacto, no los metadatos.** En el diagrama de SHAP
se ve explícito: `_matriz` consulta `feature_names_in_` del modelo. Es la corrección del
defecto que documenta el README.

**La cadena de decoradores tiene un orden fijo.** `EstrategiaConCache(EstrategiaAuditada(...))`.
El caché va por fuera, así que un acierto de caché **no** registra la inferencia. Es una
consecuencia real del orden y está dibujada en el diagrama 3 como la rama `alt`.

**El proxy virtual tiene un límite y el diagrama lo muestra.** `TreeExplainer` inspecciona el
tipo del modelo, así que no acepta el `ArtefactoDiferido`: hay que entregarle el artefacto
materializado. Es el precio de la carga diferida y aparece explícito en el diagrama 5, porque
costó un endpoint caído descubrirlo.

**El simulador consulta al Builder antes de armar la malla.** `ConstructorDeEscenario.rango_valido()`
acota los puntos para que la curva nunca proponga un valor que el propio constructor
rechazaría. Aparece en el diagrama 4.

## 06 · Vista de despliegue

`06_despliegue.png` (fuente: `06_despliegue.mmd`). Muestra las **tres unidades de despliegue** y
los cuatro cuantos logicos: la estacion de ingesta por lotes, el servidor de aplicacion —donde Q2
y Q3 comparten un solo proceso— y el nodo de estaticos, mas el servidor de base de datos.

Es el unico diagrama que representa el despliegue: los cinco anteriores son de clases y de
secuencia. Se genero para dar soporte grafico a la precision de que **Q2 y Q3 constituyen un
unico cuanto fisico** (Ford et al., 2021, cap. 2, pp. 29-30) y de que la forma resultante es un
monolito modular.

## 02a y 02b · Por qué el diagrama de patrones está además dividido

`02_patrones.png` conserva la vista completa de los doce patrones, pero su proporción es de 3,5 a 1:
al ancho de una página de tesis el texto queda por debajo de los tres puntos y resulta ilegible.
Por eso se derivaron dos vistas del mismo archivo fuente, agrupadas por cuanto de arquitectura, que
son las que se incrustan en el informe. El diagrama original no se modificó.

## 06 · Diagrama de contexto

`06_contexto.png` (fuente: `06_contexto.mmd`). Presenta el ecosistema en cuatro etapas —sistemas de
origen, capa analítica, motor predictivo y capa de servicio B2B— y rotula **cada flujo sobre el que
opera un control**, destacado en rojo. La decisión de situar los controles sobre flujos y no sobre
componentes es deliberada: un control declarado a nivel de módulo no es verificable, mientras que
uno situado sobre un flujo se comprueba observando lo que ese flujo produce.

CTRL-01, CTRL-02, CTRL-03 y CTRL-05 aparecen sobre más de un flujo, porque no son puntos únicos
sino condiciones que se sostienen a lo largo de la cadena.

> **Colisión de numeración conocida.** `06_contexto` y `06_despliegue` comparten número. El de
> despliegue se generó primero; el de contexto se numeró 06 por corresponder al sexto diagrama de
> arquitectura. Renumerar el de despliegue a `07_despliegue` es un cambio pendiente y trivial.
