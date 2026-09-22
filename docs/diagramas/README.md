# Modelo de clases y diagramas de secuencia

Los diagramas se derivaron **del código real**, no de un diseño ideal. Donde el código
no coincidía con lo esperado, se documentó lo que hay.

Los dos diagramas de datos (`00_*`) son los originales de ERDPlus y draw.io. Los de
arquitectura (`01_*` a `06_*`) tienen fuente en Mermaid (`.mmd`) más exportación a PNG para
pegar en el documento de tesis.

Documentos relacionados fuera de esta carpeta: `docs/Anexo_mapeo_conceptual_fisico.docx`
(la derivación conceptual → físico), `docs/informes/` (el informe del Hito 2, que cita estas
figuras) y `db/esquema_sned_canonico.sql` (el DDL de referencia del que se partió
`db/esquemas/`).

| # | Archivo | Qué muestra | Origen |
|---|---------|-------------|--------|
| 0 | `00_modelo_entidad_relacion.png` | Modelo conceptual: 12 entidades, especialización, atributos derivados | ERDPlus |
| 0 | `00_modelo_fisico_bd.drawio.png` | Modelo físico del dominio `core` + `hechos` | draw.io |
| 1 | `01_hexagonal` | Los cuatro puertos con sus adaptadores concretos | Mermaid |
| 2 | `02_patrones` | Los doce patrones aplicados | Mermaid |
| 2a | `02a_patrones_motor` | Los patrones del motor predictivo, derivado de `02_patrones` | Mermaid |
| 2b | `02b_patrones_servicio` | Los patrones del servicio y la ingesta, derivado de `02_patrones` | Mermaid |
| 3 | `03_secuencia_prediccion` | De la petición HTTP a la respuesta, pasando por los seis modelos | Mermaid |
| 4 | `04_secuencia_simulacion` | El what-if completo y las 54 inferencias que explican los 4,6 s | Mermaid |
| 5 | `05_secuencia_shap` | De la petición a la atribución por variable, y de dónde sale el vector | Mermaid |
| 6 | `06_contexto` | Las cuatro etapas del sistema y los cinco controles de arquitectura | Mermaid |
| 6 | `06_despliegue` | Las tres unidades de despliegue y los cuatro cuantos lógicos | Mermaid |

**Sobre el `02_patrones` partido en dos.** El original tiene razón de aspecto 3,47:1: al
ancho de una página quedaba en ~2,7 pt de cuerpo, es decir ilegible. `02a` y `02b` son
derivados suyos para el documento, no reemplazos: el original se conserva porque es el que
muestra los doce patrones juntos, y es el que cita el informe del Hito 2 como Figura 4.

**Sobre el 6 repetido.** `06_contexto` y `06_despliegue` comparten número a propósito: son
las dos figuras que el informe del Hito 2 ya entregado referencia con esos nombres exactos.
Renumerar una rompería los enlaces de un documento entregado. El prefijo aquí ordena, no
identifica.

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
