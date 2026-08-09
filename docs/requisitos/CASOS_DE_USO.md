# Casos de uso

Identificador del documento: **CU-SNED-01**

Los casos de uso describen la interacción observable entre un actor y el sistema. No describen
pantallas ni algoritmos: describen el intercambio. El diseño interno que los realiza está en
`docs/diseno/DISENO_DEL_SOFTWARE.md` y los diagramas de secuencia correspondientes en
`docs/diagramas/`.

## 1. Actores

| Actor | Naturaleza | Alcance de datos |
|-------|-----------|------------------|
| **Directivo** | Humano. Equipo directivo de un establecimiento | Un RBD |
| **Sostenedor** | Humano. Responsable de una red de establecimientos | N RBD declarados |
| **Auditor** | Humano. Verifica el cálculo y la composición del modelo | Todos los RBD, sin restricción de jurisdicción |
| **Ingeniero de datos** | Humano. Opera la ingesta y el registro de modelos | Fuera de la aplicación web: línea de comandos |
| **Motor predictivo** | Sistema. Cuanto 2 tras el puerto `EstrategiaPredictiva` | — |
| **Repositorio de datos** | Sistema. PostgreSQL o parquet tras el puerto `RepositorioEstablecimientos` | — |

## 2. Diagrama de casos de uso

```
                        ┌─────────────────────────────────────────────┐
                        │        Ecosistema predictivo SNED           │
                        │                                             │
   Directivo ──────────▶│  CU-01 Iniciar sesión                       │
        │               │  CU-02 Consultar tablero del establecimiento│◀── Motor
        ├──────────────▶│  CU-03 Revisar alertas                      │    predictivo
        ├──────────────▶│  CU-04 Simular escenario                    │◀───────┤
        └──────────────▶│  CU-05 Consultar reporte de explicabilidad  │◀───────┘
                        │                                             │
   Sostenedor ─────────▶│  CU-06 Listar establecimientos a cargo      │◀── Repositorio
        └──────────────▶│  CU-07 Consultar posición en el grupo       │    de datos
                        │                                             │
   Auditor ────────────▶│  CU-08 Auditar composición y cobertura      │
        └──────────────▶│  CU-09 Consultar catálogo de ponderaciones  │
                        │                                             │
   Ing. de datos ──────▶│  CU-10 Ingerir una fuente                   │
        ├──────────────▶│  CU-11 Publicar un artefacto en el registro │
        └──────────────▶│  CU-12 Conmutar la fuente de datos          │
                        └─────────────────────────────────────────────┘
```

Fuente editable del diagrama: pendiente de exportar a `docs/diagramas/06_casos_de_uso.mmd`.

---

## 3. Descripciones

### CU-01 · Iniciar sesión

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Directivo, Sostenedor, Auditor |
| **Requisito** | RF-01 |
| **Precondición** | El usuario existe en el directorio de autorización |
| **Disparador** | El usuario envía credenciales desde la pantalla de acceso |
| **Flujo principal** | 1. El actor envía usuario y clave. 2. El sistema valida la credencial. 3. El sistema construye un token firmado con el identificador, el rol y la lista de RBD bajo jurisdicción. 4. El sistema devuelve el token y el perfil. 5. El cliente almacena el token en memoria de sesión. |
| **Flujo alternativo A1** | Credencial inválida → el sistema responde 401 y no revela si el usuario existe |
| **Postcondición** | El cliente posee un token con vigencia de 480 minutos |
| **Requisito no funcional asociado** | RNF-03 |
| **Realización** | `q3_servicio/api/v1/routers/auth.py`, `q3_servicio/core/seguridad.py` |

### CU-02 · Consultar tablero del establecimiento

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Directivo |
| **Requisito** | RF-03, RF-04 |
| **Precondición** | Sesión iniciada; el RBD pertenece a la jurisdicción del actor |
| **Flujo principal** | 1. El actor selecciona un RBD. 2. El sistema recupera el vector de variables observadas desde el repositorio activo. 3. El sistema solicita al motor la estimación del índice y de los seis factores. 4. El motor devuelve la estimación con el desglose por factor y el aporte ponderado de cada uno. 5. El sistema devuelve la respuesta; el cliente la renderiza como tablero. |
| **Flujo alternativo A1** | El RBD no tiene registros en la base analítica → 404 con mensaje explícito. **No se imputan valores para completar la ficha** |
| **Flujo alternativo A2** | El RBD no pertenece a la jurisdicción → 403, nunca 404 |
| **Postcondición** | El actor conoce la estimación y qué proporción de ella descansa en factores acotados |
| **Diagrama de secuencia** | `docs/diagramas/03_secuencia_prediccion.png` |
| **Realización** | `routers/prediccion.py` → `servicios/motor.py` → `EstrategiaPredictiva` |

### CU-03 · Revisar alertas

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Directivo |
| **Requisito** | RF-05 |
| **Precondición** | Existe una estimación vigente para el RBD |
| **Flujo principal** | 1. El sistema construye un contexto de alerta con la estimación y las variables observadas. 2. Evalúa cada regla registrada contra el contexto. 3. Devuelve las alertas satisfechas con severidad, factor implicado y detalle accionable. |
| **Flujo alternativo A1** | Ninguna regla se satisface → se devuelve una alerta informativa "Sin alertas activas", nunca una lista vacía sin explicación |
| **Reglas implementadas** | Trampa de superación; Riesgo normativo; Caída IDPS; Factor acotado dominante |
| **Realización** | `servicios/reglas_alerta.py`; cada regla es una `Especificacion` |

### CU-04 · Simular escenario

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Directivo |
| **Requisito** | RF-07 |
| **Precondición** | La variable a mover pertenece al conjunto de variables simulables y su rango es válido |
| **Flujo principal** | 1. El actor elige una variable y un número de puntos. 2. El sistema construye el escenario base desde la observación real. 3. Genera una malla de valores dentro del rango admisible de la variable. 4. Para cada punto de la malla solicita al motor una estimación completa. 5. Devuelve la curva de sensibilidad del índice frente a la variable. |
| **Flujo alternativo A1** | La variable no es simulable → 422 con el nombre de la variable rechazada |
| **Flujo alternativo A2** | El valor sale del rango declarado → se recorta al rango, no se rechaza la petición |
| **Restricción conocida** | La respuesta toma alrededor de 4,6 s: son 54 inferencias por llamada (9 puntos × 6 modelos). Documentado y no resuelto |
| **Diagrama de secuencia** | `docs/diagramas/04_secuencia_simulacion.png` |
| **Realización** | `routers/explicabilidad.py` → `ConstructorDeEscenario` → `EstrategiaPredictiva.simular` |

### CU-05 · Consultar reporte de explicabilidad

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Directivo |
| **Requisito** | RF-06 |
| **Precondición** | El motor activo declara soportar explicabilidad |
| **Flujo principal** | 1. El actor selecciona un factor. 2. El sistema materializa el artefacto del factor —carga diferida: el modelo no se lee del disco hasta que se necesita—. 3. Calcula las atribuciones de Shapley sobre la observación. 4. Verifica la aditividad: la suma de contribuciones más el valor base debe reproducir la predicción dentro de 1e-3. 5. Traduce cada variable a una etiqueta legible. 6. Devuelve las contribuciones ordenadas por magnitud. |
| **Flujo alternativo A1** | El motor activo no soporta explicabilidad → 422, y la interfaz oculta la ventana |
| **Flujo alternativo A2** | La variable ausente se explica como "Sin medición de …", no como valor cero |
| **Diagrama de secuencia** | `docs/diagramas/05_secuencia_shap.png` |
| **Realización** | `estrategias/desagregada.py`, `etiquetas.py` |

### CU-06 · Listar establecimientos a cargo

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Sostenedor |
| **Requisito** | RF-02 |
| **Flujo principal** | 1. El sistema toma la lista de RBD del token. 2. Consulta el repositorio activo. 3. Devuelve una fila por establecimiento con índice vigente, bienio y grupo homogéneo. |
| **Invariante verificada** | Una fila por establecimiento, no una por ciclo. Ambos adaptadores devuelven el mismo contrato, con los mismos nombres de campo en minúsculas |
| **Realización** | `routers/establecimientos.py`; `RepositorioEstablecimientos.listar` |

### CU-07 · Consultar posición en el grupo homogéneo

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Sostenedor, Directivo |
| **Requisito** | RF-08 |
| **Flujo principal** | 1. El sistema identifica el grupo homogéneo del establecimiento en el periodo. 2. Calcula posición y percentil dentro de ese grupo. 3. Devuelve el tamaño del grupo junto con la posición, porque una posición sin denominador no informa. |
| **Restricción conocida** | 2,5× más lento sobre PostgreSQL: la vista recalcula funciones de ventana sobre 54.298 filas en cada consulta. Documentado y no resuelto |
| **Realización** | `hechos.v_ranking_intra_cluster` |

### CU-08 · Auditar composición y cobertura

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Auditor |
| **Requisito** | RF-10, RNF-12 |
| **Flujo principal** | 1. El sistema toma el conjunto de variables que el motor activo declara requerir. 2. Descuenta las banderas derivadas de ausencia, que no son variables de origen. 3. Contrasta ese conjunto contra las variables efectivamente disponibles en el repositorio activo. 4. Devuelve la proporción de cobertura y la lista nominal de las faltantes. |
| **Valor observado** | 35 de 43 variables presentes: 81,4 %. Las 8 faltantes son las diferencias de medición estandarizada, que se calculan en el entrenamiento y no se persisten |
| **Por qué existe este caso de uso** | Un sistema que estima sobre datos incompletos y no lo declara es un sistema que engaña. La cobertura es parte de la respuesta, no de la bitácora |
| **Realización** | `ServicioDePrediccion.diagnostico_de_cobertura` |

### CU-09 · Consultar catálogo de ponderaciones

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Auditor |
| **Requisito** | RF-09, RNF-01 |
| **Flujo principal** | 1. El sistema lee el catálogo vigente. 2. Devuelve por factor: código, nombre, peso, restricción declarada y si es accionable. |
| **Invariante** | La suma de las ponderaciones es exactamente 1,0. La base lo impone con un disparador diferido sobre `core.factor_sned`; el código lo verifica con `verificar_suma_pesos` |
| **Realización** | `routers/salud.py`, `q2_modelamiento/catalogo.py` |

### CU-10 · Ingerir una fuente

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Ingeniero de datos |
| **Requisito** | RF-11 |
| **Flujo principal** | 1. Se invoca el ingestor de la fuente. 2. La plantilla ejecuta: leer, normalizar el identificador, aplicar reglas de admisión, particionar en admitidos y cuarentena, persistir ambos, emitir reporte de calidad. 3. Si la cobertura de llave cae bajo el umbral, el reporte lo declara. |
| **Regla no negociable** | Los registros que no satisfacen las reglas **van a cuarentena, no al descarte**. Un dato rechazado sigue siendo evidencia |
| **Realización** | `q1_ingesta/ingestor.py` (Template Method), `q1_ingesta/reglas.py` (Specification) |

### CU-11 · Publicar un artefacto en el registro

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Ingeniero de datos |
| **Requisito** | RF-12, RNF-06 |
| **Flujo principal** | 1. El artefacto entrenado se deposita en el registro con sus metadatos. 2. El registro expone inventario: nombre, tamaño, estado de materialización y métricas. 3. El servicio solo carga el artefacto cuando la primera petición lo exige. |
| **Deuda declarada** | Los metadatos no registran la versión de la librería. Medido: los artefactos se serializaron con scikit-learn 1.6.1 y el entorno de servicio fija 1.5.2 |
| **Realización** | `q2_modelamiento/registro_modelos.py`, `artefactos.py` |

### CU-12 · Conmutar la fuente de datos

| Campo | Contenido |
|-------|-----------|
| **Actor principal** | Ingeniero de datos |
| **Requisito** | RF-13, RNF-04 |
| **Flujo principal** | 1. Se fija la variable de entorno que nombra el adaptador. 2. La fábrica resuelve la implementación del puerto. 3. El servicio opera sin conocer cuál quedó activo. |
| **Criterio de aceptación** | Las mismas llamadas contra ambos adaptadores producen respuestas equivalentes campo por campo, y **todas ellas exitosas**: dos adaptadores pueden coincidir en estar rotos |
| **Realización** | `q3_servicio/repositorios/fabrica.py` |
