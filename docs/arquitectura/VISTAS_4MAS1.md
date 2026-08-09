# Modelo 4+1: vistas de la arquitectura

Identificador del documento: **V41-SNED-01**
Referencia: Kruchten, P. (1995). *Architectural Blueprints — The 4+1 View Model of Software
Architecture*. IEEE Software 12(6), 42-50.

El modelo 4+1 organiza la arquitectura en cuatro vistas concurrentes más una quinta que las
articula. La razón de usarlo aquí no es formal: cada vista responde la pregunta de un
interlocutor distinto, y en una defensa esas preguntas llegan por separado.

| Vista | Pregunta que responde | Interlocutor |
|-------|----------------------|--------------|
| Lógica | ¿Qué abstracciones existen y cómo se relacionan? | Diseñador |
| De procesos | ¿Qué corre concurrentemente y qué espera a qué? | Integrador |
| De desarrollo | ¿Cómo se organiza el código y quién puede importar a quién? | Programador |
| Física | ¿Dónde se ejecuta cada parte? | Operador |
| +1 · Escenarios | ¿Todo lo anterior sirve para algo concreto? | Todos |

---

## 1. Vista lógica

Describe la descomposición funcional del dominio. El elemento organizador no es la clase sino
el **puerto**: una abstracción cuyo propósito es aislar una dimensión de cambio.

### Los cuatro puertos

| Puerto | Dimensión de cambio que aísla | Implementaciones |
|--------|-------------------------------|------------------|
| `Especificacion[T]` | Reglas de negocio que cambian por normativa | Reglas de admisión de ingesta; reglas de alerta |
| `IngestorDeFuente` | Formato y codificación de cada fuente pública | Excel, CSV latin-1, CSV UTF-8 |
| `EstrategiaPredictiva` | El algoritmo de estimación | Desagregada por factor; global |
| `RepositorioEstablecimientos` | El medio de persistencia | Parquet; PostgreSQL |

### Entidades del dominio

```
Establecimiento ──1:N── EstablecimientoPeriodo ──N:1── Periodo
       │                          │
       │                          └──N:1── GrupoHomogeneo
       │
       ├──1:N── ResultadoIndice ──1:N── FactorMedido ──N:1── FactorSned
       ├──1:N── MedicionEstandarizada  (formato largo)
       ├──1:N── MedicionDesarrollo     (formato largo)
       ├──1:N── IndicadorAnual         (formato largo, genérico)
       └──1:N── EventoAgregado         (ventana temporal declarada)
```

Cuatro decisiones sostienen esta vista y están documentadas en `docs/adr/`:

1. El índice **no** es un atributo del establecimiento: es un resultado fechado (ADR-005).
2. El grupo homogéneo **no** es estable: se indexa por periodo, porque el 35,1 % de los
   establecimientos cambia de agrupación entre ciclos.
3. Las ponderaciones son dato de catálogo, no constantes (ADR-005).
4. Los indicadores anuales usan una tabla genérica: añadir una fuente inserta filas, no altera
   el esquema.

Modelo de clases completo: `docs/diagramas/01_hexagonal.png` y `02_patrones.png`.
Detalle de responsabilidades: `docs/diseno/DISENO_DEL_SOFTWARE.md`.

---

## 2. Vista de procesos

Describe qué ocurre en tiempo de ejecución: hilos, latencia, sincronización.

### Procesos vivos

| Proceso | Naturaleza | Estado que mantiene |
|---------|-----------|--------------------|
| Servidor de aplicación (uvicorn) | Un proceso, bucle de eventos asíncrono | Configuración en caché, registro de artefactos, caché de estrategia |
| Motor de base de datos | Proceso independiente | Toda la persistencia |
| Servidor de desarrollo del cliente | Proceso independiente | Ninguno |
| Ingesta | Proceso por lotes, invocado a mano | Ninguno entre ejecuciones |

### Carga diferida como decisión de proceso

Los artefactos de modelo pesan 210 MB. Cargarlos al arrancar convertiría cada reinicio en una
espera de decenas de segundos para servir peticiones que quizá no necesiten ningún modelo. El
`ArtefactoDiferido` los materializa en la primera petición que los exija y los conserva. El
costo se paga una vez y solo si alguien lo provoca.

Consecuencia observable: **la primera petición de predicción de cada arranque es lenta**; las
siguientes no. Esto no es un defecto intermitente, es el comportamiento diseñado.

### Latencias medidas

| Operación | Tiempo | Comentario |
|-----------|--------|-----------|
| Autenticación | < 50 ms | Firma simétrica |
| Predicción (artefactos ya materializados) | < 300 ms | Seis inferencias |
| Listado de establecimientos | < 200 ms | Una consulta con `DISTINCT ON` |
| Explicación SHAP | < 500 ms | Explicador exacto sobre árboles |
| **Simulación** | **≈ 4,6 s** | 54 inferencias por llamada (9 puntos × 6 modelos). El caché no ayuda: cada punto es una observación distinta. **Declarado, no resuelto** |
| **Ordenamiento intragrupo** | **2,5× más lento en PostgreSQL** | La vista recalcula funciones de ventana sobre 54.298 filas en cada consulta. **Declarado, no resuelto** |

Ambas limitaciones se dejan visibles por decisión explícita: una arquitectura que oculta sus
puntos lentos obliga a redescubrirlos en producción.

### Concurrencia

No hay estado mutable compartido entre peticiones salvo dos cachés de solo lectura tras la
primera escritura: el registro de artefactos y la configuración. La sesión de base de datos se
toma y se devuelve dentro del ámbito de cada petición.

---

## 3. Vista de desarrollo

Describe la organización estática del código y las reglas de dependencia.

```
indice-sned/
├── quanta/
│   ├── compartido/        lo que los cuatro cuantos necesitan por igual
│   ├── q1_ingesta/        único autorizado a leer archivos crudos
│   ├── q2_modelamiento/   único que conoce scikit-learn y shap
│   ├── q3_servicio/       encapsula el motor tras HTTP; prohibido importar ML
│   └── q4_cliente/        consume JSON tipado; cero acoplamiento de código
├── db/                    DDL versionado y vistas
├── scripts/               inicialización, carga y verificación
├── tests/                 por tipo en el primer nivel, por cuanto adentro
├── contratos/             el catálogo de factores como dato
├── models/                registro de artefactos y metadatos
└── docs/                  esta documentación
```

### Grafo de dependencias permitido

```
q1_ingesta      ──▶ compartido
q2_modelamiento ──▶ compartido
q3_servicio     ──▶ q2_modelamiento, compartido
q4_cliente      ──▶ (solo HTTP/JSON)
```

La regla no es una convención escrita: `scripts/verificar_arquitectura.py` recorre los
`import` reales y falla si alguno sale del grafo. La misma verificación corre como prueba en
`tests/arquitectura/test_fronteras_de_cuantos.py`, de modo que una violación rompe la suite,
no solo la disciplina.

### Estructura de las pruebas

Híbrida: por tipo en el primer nivel, por cuanto adentro. Marcadores declarados en
`pyproject.toml`: `datos`, `modelo`, `api`, `paridad`, `requiere_datos`, `requiere_bd`. Los dos
últimos permiten ejecutar la suite en integración continua sin base de datos ni artefactos.

---

## 4. Vista física

Describe el despliegue. El detalle completo, con la separación entre servidor de base de datos
y servidor de aplicación, está en `PLATAFORMA_DE_OPERACION.md`.

```
┌──────────────┐  HTTPS   ┌────────────────────┐  TCP 5432  ┌─────────────────┐
│  Navegador   │─────────▶│ Servidor de        │───────────▶│ Servidor de     │
│  (cliente)   │◀─────────│ aplicación         │◀───────────│ base de datos   │
└──────────────┘   JSON   │ FastAPI + uvicorn  │   SQL      │ PostgreSQL 16   │
                          │ registro artefactos│            │ 38 tablas       │
                          └────────────────────┘            └─────────────────┘
                                    ▲
                                    │ lectura, fuera de línea
                          ┌────────────────────┐
                          │ Proceso de ingesta │
                          │ (por lotes)        │
                          └────────────────────┘
```

El cuanto 4 se compila a archivos estáticos: no necesita servidor de aplicación propio.

---

## 5. Vista +1: escenarios

Los escenarios son los casos de uso ejecutados de punta a punta. Su función en el modelo 4+1 es
validar que las otras cuatro vistas encajan: un escenario que no se puede recorrer sobre las
vistas indica que falta un elemento en alguna.

| Escenario | Vistas que atraviesa | Artefacto que lo documenta |
|-----------|---------------------|----------------------------|
| CU-02 Consultar tablero | Lógica → procesos → física | `docs/diagramas/03_secuencia_prediccion.png` |
| CU-04 Simular escenario | Lógica → procesos (aquí aparece la latencia de 4,6 s) | `docs/diagramas/04_secuencia_simulacion.png` |
| CU-05 Reporte de explicabilidad | Lógica → procesos (aquí aparece la carga diferida) | `docs/diagramas/05_secuencia_shap.png` |
| CU-12 Conmutar la fuente | Desarrollo → física | `tests/paridad/` |

El escenario CU-12 es el que valida la arquitectura entera: si el puerto de repositorio está
bien trazado, cambiar de parquet a PostgreSQL no debe alterar ninguna respuesta. Se midió: 141
llamadas, cero divergencias. Cuando falló, no falló la arquitectura sino tres supuestos del
arnés de prueba, y ese hallazgo está documentado en `docs/planes/PLAN_INTEGRACION.md`.
