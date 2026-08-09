# Matriz de trazabilidad de requerimientos

Identificador del documento: **MT-SNED-01**

La matriz responde una sola pregunta, en las dos direcciones: **dónde vive cada requisito** y
**por qué existe cada componente**. Un componente que no aparece en la columna de diseño de
ningún requisito es código sin mandato, y hay que justificarlo o borrarlo.

Se compone de cuatro tramos encadenados:

```
Requisito ──▶ Caso de uso ──▶ Componente de diseño ──▶ Unidad de código ──▶ Prueba
```

---

## 1. Matriz principal: requisitos funcionales

| Requisito | Caso de uso | Componente de diseño | Unidad de código | Prueba que lo verifica |
|-----------|-------------|----------------------|------------------|------------------------|
| RF-01 | CU-01 | Módulo de autorización del cuanto 3 | `q3_servicio/core/seguridad.py`, `api/v1/routers/auth.py` | `tests/integracion/q3/test_api_y_rbac.py` |
| RF-02 | CU-06 | Puerto `RepositorioEstablecimientos`, operación `listar` | `repositorios/contrato.py`, `parquet.py`, `postgres.py` | `tests/paridad/test_paridad_adaptadores.py` |
| RF-03 | CU-02 | Puerto `RepositorioEstablecimientos`, operación `obtener` | `repositorios/postgres.py` (consulta de reconstrucción ancha) | `tests/unitarias/q3/test_repositorio_y_alertas.py` |
| RF-04 | CU-02 | Puerto `EstrategiaPredictiva` + fachada `ServicioDePrediccion` | `q2_modelamiento/contrato.py`, `estrategias/desagregada.py`, `estrategias/global_hgb.py`, `q3_servicio/servicios/motor.py` | `tests/unitarias/q2/test_contrato_del_indice.py` |
| RF-05 | CU-03 | Conjunto de reglas de alerta como especificaciones componibles | `q3_servicio/servicios/reglas_alerta.py` | `tests/unitarias/q3/test_repositorio_y_alertas.py` |
| RF-06 | CU-05 | Operación `explicar` del puerto predictivo + traductor de etiquetas | `estrategias/desagregada.py`, `q2_modelamiento/etiquetas.py` | `tests/unitarias/q2/test_contrato_del_indice.py` |
| RF-07 | CU-04 | Constructor de escenarios + operación `simular` | `q2_modelamiento/escenario.py`, `estrategias/desagregada.py` | `tests/unitarias/q2/test_patrones_del_motor.py` |
| RF-08 | CU-07 | Vista de ordenamiento intragrupo + operación `ranking` | `db/vistas/02_v_ranking_intra_cluster.sql`, `repositorios/postgres.py` | Verificación manual documentada; excluido de paridad por diseño |
| RF-09 | CU-09 | Catálogo de factores como dato | `contratos/catalogo_factores.json`, `core.factor_sned`, `q2_modelamiento/catalogo.py` | `tests/unitarias/q2/test_contrato_del_indice.py` |
| RF-10 | CU-08 | Diagnóstico de cobertura de la fachada | `q3_servicio/servicios/motor.py` | `tests/integracion/q3/test_contrato_openapi.py` |
| RF-11 | CU-10 | Plantilla de ingesta + reglas de admisión | `q1_ingesta/ingestor.py`, `reglas.py`, `calidad.py` | `tests/integracion/q1/test_pipeline_calidad.py`, `tests/unitarias/q1/test_reglas_y_plantilla.py` |
| RF-12 | CU-11 | Registro de modelos + artefacto diferido | `q2_modelamiento/registro_modelos.py`, `artefactos.py` | `tests/unitarias/q2/test_patrones_del_motor.py` |
| RF-13 | CU-12 | Fábrica de adaptadores del puerto de repositorio | `q3_servicio/repositorios/fabrica.py` | `tests/paridad/test_paridad_adaptadores.py` |

## 2. Matriz de requisitos no funcionales

| Requisito | Mecanismo de diseño que lo materializa | Unidad de código o esquema | Evidencia |
|-----------|----------------------------------------|----------------------------|-----------|
| RNF-01 | El cálculo oficial expresado como vista SQL auditable | `db/vistas/01_v_indicer_reconstruido.sql` | Discrepancia máxima 0,0006 sobre 44.679 filas |
| RNF-02 | Contrato de explicación con verificación de aditividad | `q2_modelamiento/contrato.py` | `verificar_aditividad(1e-3)` |
| RNF-03 | Autorización por jurisdicción antes de tocar el repositorio | `core/seguridad.py::exigir_jurisdiccion` | CTRL-04 |
| RNF-04 | Puerto con dos adaptadores intercambiables por configuración | `repositorios/` | INT-05: 141 llamadas, 0 divergencias |
| RNF-05 | Frontera Strategy entre servicio y algoritmo | `q2_modelamiento/contrato.py` | Tres arquitecturas comparadas sin tocar el servicio |
| RNF-06 | Registro versionado + tablas de inferencia y atribución | `ml.modelo`, `ml.inferencia`, `ml.inferencia_atribucion` | CTRL-05 |
| RNF-07 | Cuarentena en lugar de descarte; formato largo sin relleno | `q1_ingesta/calidad.py`, `hechos.*` | CTRL-01; 68,8 % de nulos estructurales declarados |
| RNF-08 | Medición comparativa entre adaptadores, con las excepciones declaradas | — | Dos limitaciones documentadas y no resueltas |
| RNF-09 | Interfaz sin dependencias de motor específico | `q4_cliente/` | PPC-SNED-01 |
| RNF-10 | Grafo de dependencias entre cuantos verificado por script | `scripts/verificar_arquitectura.py` | `tests/arquitectura/test_fronteras_de_cuantos.py` |
| RNF-11 | DDL versionado + carga idempotente con `ON CONFLICT` | `db/`, `scripts/cargar_bd.py` | `docs/manuales/MANUAL_INSTALACION.md` |
| RNF-12 | Campo `es_acotado` propagado hasta la interfaz | `q2_modelamiento/catalogo.py`, `q4_cliente/src/paginas/Dashboard.tsx` | 63 % de la ponderación marcada como acotada |

## 3. Trazabilidad inversa: por qué existe cada componente

| Componente | Requisito que lo justifica | Si se borrara |
|------------|---------------------------|---------------|
| `compartido/especificacion.py` | RF-05, RF-11 | Las reglas de admisión y de alerta dejarían de ser componibles y volverían a ser condicionales anidados |
| `q1_ingesta/ingestor.py` | RF-11 | Cada fuente reimplementaría el mismo orden de pasos, con divergencias silenciosas |
| `q2_modelamiento/decoradores.py` | RNF-06, RNF-08 | Auditoría y caché tendrían que incrustarse en cada estrategia |
| `q2_modelamiento/artefactos.py` | RNF-08 | El arranque del servicio cargaría 145 MB de artefactos que quizá nadie pida |
| `q2_modelamiento/escenario.py` | RF-07 | La construcción de escenarios quedaría dispersa en el router, sin validación de rango |
| `q3_servicio/repositorios/parquet.py` | RNF-04, RNF-11 | Se perdería la capacidad de demostrar el sistema sin base de datos, y la paridad dejaría de tener contra qué comparar |
| `q3_servicio/servicios/motor.py` | RF-04, RF-10 | Los routers hablarían directamente con el motor y el cuanto 3 se acoplaría al 2 |
| `hechos.v_indicer_reconstruido` | RNF-01 | La auditoría del cálculo dependería de ejecutar Python |
| `core.conjunto_entrenamiento` | RES-01 | Se perdería la lista maestra del conjunto depurado y el pivote de entrenamiento cambiaría de población entre ejecuciones |
| `tests/paridad/` | RNF-04 | La conmutación de fuente sería una promesa sin evidencia |

## 4. Cobertura por integración

| Integración | Frontera | Estado | Artefacto |
|-------------|----------|--------|-----------|
| INT-01 | Q1 → Q2 | Cubierto | `tests/integracion/q1/test_pipeline_calidad.py` |
| INT-02 | Q2 → Q3 | Cubierto | `tests/integracion/q3/test_api_y_rbac.py` |
| INT-03 | Q3 → PostgreSQL | Cubierto | Adaptador verificado contra la base cargada |
| INT-04 | Q3 → Q4 | Cubierto | `tests/integracion/q3/test_contrato_openapi.py` |
| INT-05 | Parquet ↔ PostgreSQL | Cubierto | 141 llamadas, 0 divergencias, ejecutable sin base ni artefactos |

## 5. Requisitos sin cobertura automatizada

Se declaran en lugar de omitirse. Una matriz sin huecos suele ser una matriz maquillada.

| Requisito | Estado | Motivo | Compensación |
|-----------|--------|--------|--------------|
| RF-08 | Verificación manual | La consulta de ordenamiento se excluyó de la comparación entre adaptadores por diferencias legítimas de desempate | Consulta de verificación documentada |
| RNF-09 | Sin implementar | Requiere ejecutar la interfaz sobre tres motores de navegador | Plan PPC-SNED-01 redactado, matriz manual definida |
| CU-01 a CU-07 como escenarios de aceptación | Sin implementar | Los escenarios están redactados en Gherkin pero falta la capa que los ejecuta | Plan PPA-SNED-01 |
