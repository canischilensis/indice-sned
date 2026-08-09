# Catálogo de requisitos

Identificador del documento: **CR-SNED-01**
Estado: línea base. Todo cambio pasa por `docs/gestion/PLAN_GESTION_CAMBIOS.md`.

Cada requisito se enuncia de forma verificable: si no se puede escribir una prueba que lo
falsee, no es un requisito, es una intención. La columna *Verificación* nombra el artefacto
que lo comprueba; la matriz de trazabilidad (`MATRIZ_TRAZABILIDAD.md`) cierra el circuito
hasta el archivo de código.

El origen de los requisitos está en `docs/CUESTIONARIO_REQUISITOS.md`, en el Capítulo 3 de la
tesis y en el Informe Técnico del índice.

---

## 1. Requisitos funcionales

| ID | Requisito | Actor | Prioridad | Verificación |
|----|-----------|-------|-----------|--------------|
| RF-01 | El sistema autentica a un usuario y emite un token firmado que transporta su rol y la lista de RBD bajo su jurisdicción | Sostenedor, Directivo, Auditor | Alta | `tests/integracion/q3/test_api_y_rbac.py` |
| RF-02 | El sistema lista los establecimientos que el usuario autenticado tiene derecho a ver, con su índice vigente y su grupo homogéneo | Sostenedor | Alta | `GET /api/v1/establecimientos`; prueba de paridad INT-05 |
| RF-03 | El sistema entrega el vector de variables observadas de un establecimiento para un periodo | Directivo | Alta | `GET /api/v1/establecimientos/{rbd}` |
| RF-04 | El sistema estima el índice SNED y los seis factores que lo componen, reconstruyendo el índice con las ponderaciones vigentes | Directivo, Sostenedor | Alta | `GET /api/v1/prediccion/{rbd}`; `tests/unitarias/q2/test_contrato_del_indice.py` |
| RF-05 | El sistema emite alertas tipificadas sobre la estimación, con severidad y factor implicado | Directivo | Media | `GET /api/v1/prediccion/{rbd}/alertas`; `tests/unitarias/q3/test_repositorio_y_alertas.py` |
| RF-06 | El sistema explica la estimación de un factor mediante atribución de Shapley, con verificación de aditividad | Directivo | Alta | `GET /api/v1/xai/{rbd}/shapley` |
| RF-07 | El sistema simula el efecto de mover una variable sobre el índice, devolviendo una curva de sensibilidad | Directivo | Alta | `POST /api/v1/xai/simular` |
| RF-08 | El sistema entrega la posición y el percentil del establecimiento dentro de su grupo homogéneo del periodo | Sostenedor | Media | `GET /api/v1/establecimientos/{rbd}/ranking` |
| RF-09 | El sistema publica el catálogo de factores y ponderaciones vigentes como dato consultable | Auditor | Alta | `GET /api/v1/catalogo/factores` |
| RF-10 | El sistema reporta qué proporción de las variables que el modelo requiere está efectivamente disponible en la fuente activa | Auditor | Alta | `GET /api/v1/salud/composicion` |
| RF-11 | El sistema ingiere fuentes públicas heterogéneas, deriva a cuarentena los registros que no satisfacen las reglas y emite un reporte de calidad | Ingeniero de datos | Alta | `tests/integracion/q1/test_pipeline_calidad.py` |
| RF-12 | El sistema mantiene un registro de artefactos de modelo con sus metadatos, métricas e hiperparámetros | Ingeniero de datos | Media | `GET /api/v1/salud/registro`; esquema `ml` |
| RF-13 | El sistema permite conmutar la fuente de datos entre archivo columnar y base relacional sin modificar código de dominio | Ingeniero de datos | Alta | `tests/paridad/test_paridad_adaptadores.py` |

## 2. Requisitos no funcionales

| ID | Atributo de calidad | Requisito | Métrica / criterio | Verificación |
|----|--------------------|-----------|--------------------|--------------|
| RNF-01 | Auditabilidad | El cálculo del índice debe poder reproducirse desde el dato persistido, sin ejecutar código de aplicación | La vista `hechos.v_indicer_reconstruido` reproduce el índice oficial con discrepancia máxima ≤ 0,001 | Consulta documentada en `docs/diseno/DISENO_BASE_DATOS.md` |
| RNF-02 | Explicabilidad | Toda estimación debe poder descomponerse en contribuciones por variable | `ExplicacionLocal.verificar_aditividad(tolerancia=1e-3)` devuelve verdadero | `tests/unitarias/q2/test_contrato_del_indice.py` |
| RNF-03 | Seguridad | Un usuario solo accede a los RBD de su jurisdicción; la respuesta a un RBD ajeno es 403, nunca 404 | Cero accesos fuera de jurisdicción | CTRL-04; `tests/integracion/q3/test_api_y_rbac.py` |
| RNF-04 | Portabilidad de datos | La fuente de datos debe ser sustituible por configuración | Dos adaptadores del mismo puerto, 141 llamadas, 0 divergencias | INT-05 |
| RNF-05 | Sustituibilidad del algoritmo | Cambiar el algoritmo predictivo no debe tocar la capa de servicio | Tres arquitecturas comparadas sobre la misma capa | Patrón Strategy; ADR-002 |
| RNF-06 | Trazabilidad | Toda inferencia servida debe poder asociarse a la versión del artefacto que la produjo | Registro con versión por artefacto | CTRL-05; `ml.inferencia` |
| RNF-07 | Integridad del dato | No se imputan filas inexistentes: si una fuente no cubre un establecimiento, la fila no existe | 68,8 % de nulos estructurales declarados, no rellenados | CTRL-01; formato largo |
| RNF-08 | Rendimiento | Las consultas de lectura responden bajo un segundo; las excepciones se declaran | Ver limitaciones conocidas en `docs/arquitectura/VISTAS_4MAS1.md` | Medición comparativa entre adaptadores |
| RNF-09 | Compatibilidad | La interfaz opera sobre los tres motores de navegador vigentes | Plan PPC-SNED-01 | `docs/planes/PLAN_COMPATIBILIDAD.md` |
| RNF-10 | Mantenibilidad | Las fronteras entre cuantos son verificables por máquina, no por convención | `scripts/verificar_arquitectura.py` retorna 0 | `tests/arquitectura/test_fronteras_de_cuantos.py` |
| RNF-11 | Reproducibilidad | El entorno de ejecución debe poder reconstruirse desde el repositorio | `requirements.txt` + DDL versionado + carga idempotente | `docs/manuales/MANUAL_INSTALACION.md` |
| RNF-12 | Transparencia epistémica | El sistema declara qué parte de la ponderación está acotada por información no publicada | Campo `es_acotado` en cada respuesta; 63 % de la ponderación marcada | `contratos/catalogo_factores.json` |

## 3. Restricciones de diseño impuestas

No son requisitos negociables sino condiciones de contorno. Se listan porque explican
decisiones que de otro modo parecen arbitrarias.

| ID | Restricción | Motivo |
|----|-------------|--------|
| RES-01 | Los seis factores y el índice oficial no pueden usarse como variables de entrada de ningún modelo | Fuga de objetivo: son la variable que se quiere estimar |
| RES-02 | Las ponderaciones viven en catálogo, nunca en código | Volatilidad normativa por ciclo político |
| RES-03 | La ventana temporal del dato se declara en el esquema, no en un script | La regla anti-fuga debe ser estructural |
| RES-04 | Las columnas derivadas no se persisten | Anomalías de actualización |
| RES-05 | El cuanto de servicio no puede importar librerías de aprendizaje automático | Frontera de despliegue independiente |
| RES-06 | No se implementa orquestación de MLOps | El fenómeno es bianual; la infraestructura sería deuda técnica pura (ADR-003) |

## 4. Fuera de alcance declarado

| Elemento | Por qué queda fuera |
|----------|--------------------|
| Reentrenamiento automático | Periodicidad bianual del índice (ADR-003) |
| Persistencia de usuarios en base de datos | El directorio RBAC vive en memoria; el esquema `app.usuario` está creado y la migración es trabajo declarado |
| Publicación de las fichas de autorreporte | El organismo emisor no las publica; es el origen de la frontera de información |
| Cálculo oficial del beneficio monetario | El sistema estima el índice, no reemplaza el acto administrativo |
