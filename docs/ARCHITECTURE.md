# Arquitectura del ecosistema predictivo SNED

Documento vivo. Traza cada decision estructural del repositorio a su fundamento
en el Capitulo 3 de la tesis (Bloques II, III y IV) y al hallazgo del informe tecnico
que la valida.

---

## 1. Motor de la arquitectura (architectural drivers)

| Driver | Origen | Consecuencia estructural |
|--------|--------|--------------------------|
| Auditabilidad del calculo de tramos financieros | El SNED tiene consecuencia monetaria directa | Se acepta mayor complejidad distribuida a cambio de trazabilidad (Primera Ley de la Arquitectura) |
| Volatilidad normativa del MINEDUC | Los criterios de subvencion cambian por ciclo politico | Ponderaciones como dato de catalogo, Patron Strategy, dimension de cambio lento |
| Explicabilidad como requisito funcional | El directivo necesita saber **que** mover, no solo cuanto va a obtener | Motor desagregado por factor; SHAP e ICE en el nucleo, no como anexo |
| Periodicidad bianual del fenomeno | El indice se calcula cada dos anios | **Exclusion deliberada de MLOps**; verificacion programada en su lugar |
| Heterogeneidad y entropia del dato publico | 11 fuentes, formatos dispares, publicacion sin clasificar | Cuarentena en vez de descarte; formato largo; indicadores de ausencia |

---

## 2. Cuantos de arquitectura

Un cuanto es una unidad desplegable de forma independiente, con alta cohesion funcional
y acoplamiento estatico y dinamico controlado (Ford et al., 2021).

### Q1 — `q1_ingesta`
Unico cuanto autorizado a tocar archivos crudos. Entrega parquet normalizado.
**No conoce** el motor predictivo ni FastAPI.

### Q2 — `q2_modelamiento`
Unico cuanto que conoce scikit-learn, TensorFlow y shap. Expone `EstrategiaPredictiva`.
Contiene el registro de artefactos (CTRL-05), el protocolo de validacion (CTRL-02)
y la verificacion de deriva (CTRL-03).

### Q3 — `q3_servicio`
Encapsula el motor tras HTTP. Aplica RBAC (CTRL-04). **Prohibido importar librerias de ML**:
la prueba `tests/arquitectura/test_fronteras_de_cuantos.py` lo verifica en cada ejecucion de la suite.

### Q4 — `q4_cliente`
Tres ventanas funcionales. Consume exclusivamente JSON tipado. Desconoce por completo
que algoritmo esta detras.

### Grafo de dependencias permitido

```
q1_ingesta  ---> compartido
q2_modelamiento ---> compartido
q3_servicio ---> q2_modelamiento, compartido
q4_cliente  ---> (solo HTTP/JSON, cero acoplamiento de codigo)
```

`quanta/compartido/` contiene unicamente lo que los cuatro cuantos necesitan por igual
y que no pertenece a ninguno: la resolucion de rutas del proyecto. Un cuanto que importa
a otro fuera de este grafo hace fallar `scripts/verificar_arquitectura.py`, y con el la
primera compuerta de la Definicion de Terminado.

### La frontera Strategy

```python
# quanta/q2_modelamiento/contrato.py
class EstrategiaPredictiva(ABC):
    def predecir(self, observacion) -> Prediccion
    def explicar(self, observacion, factor) -> ExplicacionLocal
    def simular(self, observacion, variable, rango) -> CurvaSensibilidad
```

Verificacion empirica: durante el desarrollo se compararon tres arquitecturas
(HistGradientBoosting, Perceptron multicapa, Random Forest) sobre la misma representacion
de entrada **sin alterar la capa de servicio**. Esa es la prueba de que el patron sostiene.

---

## 3. Persistencia: seis decisiones de normalizacion

Volcar la tabla ancha del modelamiento habria perpetuado nulos estructurales y anomalias
de actualizacion. El esquema responde a seis decisiones, cada una anclada a un hallazgo:

| # | Decision | Hallazgo que la justifica | Implementacion |
|---|----------|---------------------------|----------------|
| 1 | Formato largo para mediciones e indicadores | 68,8 % de nulos estructurales en las columnas de 2do medio | `hechos.simce_medicion`, `hechos.idps_medicion`, `hechos.indicador_anual` |
| 2 | Grupo homogeneo indexado por periodo | 35,1 % de los establecimientos cambia de agrupacion entre ciclos | `hechos.sned_resultado.cluster_codigo` |
| 3 | Ponderaciones como dato de catalogo | La formula oficial se verifico con R2 = 1,0000 y MAE = 0,000 | `core.factor_sned` + `contratos/catalogo_factores.json` |
| 4 | Dimension de cambio lento | Migracion municipal hacia los SLEP altera la dependencia sin cambiar el RBD | `core.establecimiento_periodo` |
| 5 | Ventanas temporales declaradas | La regla anti-fuga debe ser estructural, no un comentario en un script | `core.ventana_sie` |
| 6 | Tabla generica de indicadores anuales | Anadir una fuente debe insertar registros, no alterar el esquema | `hechos.indicador_anual` + `core.tipo_indicador` |

El esquema tiene **38 tablas**: `core` 16, `hechos` 6, `ml` 8 y `app` 8. Las 21 de `core` y
`hechos` derivan del modelo entidad-relación; `core.conjunto_entrenamiento` —la lista maestra
del conjunto depurado— más `ml` y `app` no provienen del diagrama y se declaran como
infraestructura.

### Vistas de consumo

- `hechos.v_indicer_reconstruido` — la formula oficial como consulta auditable
- `hechos.v_ranking_intra_cluster` — posicion y percentil dentro del grupo del periodo (mecanica real del beneficio)
- `ml.mv_matriz_entrenamiento` — materializada por el costo del pivote y la naturaleza estatica del dato

---

## 3.bis Patrones de diseño

Doce patrones aplicados y doce evaluados y descartados, con la fuerza que justifica cada uno
y su fuente citada, en **`docs/PATRONES_DE_DISENO.md`**. Resumen por cuanto:

| Cuanto | Patrones |
|--------|----------|
| Q1 · Ingesta | Template Method, Specification, Adapter, Pipes and Filters |
| Q2 · Modelamiento | Strategy, Decorator, Factory Method, Registry, Virtual Proxy, Builder |
| Q3 · Servicio | Repository, Facade, Adapter, Specification |
| Q4 · Cliente | ninguno de dominio, por diseño |

Los creacionales y estructurales se concentran en Q2, donde vive la complejidad algorítmica y
los artefactos costosos; los de comportamiento en Q1 y Q3, donde viven las reglas que cambian
por normativa.

## 4. Controles de arquitectura

| ID | Riesgo mitigado | Flujo | Evidencia generada |
|----|-----------------|-------|--------------------|
| CTRL-01 | Orfandad e integridad referencial | Ingesta | `data/interim/cuarentena/*.parquet` + `ReporteCalidad` |
| CTRL-02 | Fuga de datos | Preprocesamiento y entrenamiento | Excepcion `FugaDeDatos` + R2 del predictor trivial ~ 0 |
| CTRL-03 | Deriva postpandemia | Verificacion bianual | `models/metadata/` (linea base de distribuciones, pendiente de generar) + `ml.drift_registro` |
| CTRL-04 | Acceso no autorizado | Servicio y visualizacion | `app.auditoria` + pruebas de RBAC |
| CTRL-05 | Perdida de trazabilidad | Registro de modelos | Artefactos versionados + `ml.inferencia` / `ml.inferencia_atribucion` |

---

## 5. Compuerta de incorporacion del incremento

Un incremento pasa a *Terminado* solo si supera, en orden, tres barreras:

1. **Codigo y estructura de datos** — `ruff`, `mypy`, esquema de BD, auditoria anti-fuga
2. **Criterios de aceptacion** — pruebas de integracion; un fallo de RBAC reprueba la barrera
3. **Umbral de precision** — el modelo candidato solo se aprueba si su R2 supera al vigente
   **y** la superioridad se sostiene con intervalos de confianza y prueba t pareada

Si falla cualquiera: el incremento se rechaza, retorna al Product Backlog y se preserva
la ultima version estable de los artefactos serializados.

---

## 6. Trade-offs asumidos y declarados

| Trade-off | Se gana | Se paga | Decision |
|-----------|---------|---------|----------|
| Motor desagregado vs. global | Trazabilidad variable -> factor -> indice | 0,054 de R2 | Conservar ambos con funciones distintas |
| Complejidad distribuida | Auditabilidad y despliegue independiente | Latencia de red, mas piezas moviles | Aceptado (Primera Ley) |
| Sin MLOps | Cero deuda tecnica de orquestacion | Reentrenamiento manual bianual | Aceptado: el fenomeno es bianual |
| Preprocesamiento uniforme en el benchmark | Validez interna de la comparacion | Neutraliza el manejo nativo de nulos de HistGB | Aceptado; el desempeno reportado es cota inferior |
| HistGB sobre MLP | Shapley exacto, sin GPU, serializacion simple | ~0,007 de R2 (estadisticamente equivalente) | Criterio arquitectonico, no metrico |

---

## 7. Frontera de informacion irreducible

Cinco de los seis factores estan acotados por informacion que no se publica.
Esto **no es un defecto del modelo**: es un diagnostico verificable sobre las condiciones
de replicabilidad externa del calculo estatal, y la interfaz debe comunicarlo.

| Factor | Peso | R2 | Restriccion |
|--------|------|-----|-------------|
| Efectividad | 37 % | 0,832 | ninguna |
| Superacion | 28 % | 0,200 | correccion por significancia estadistica no publica |
| Igualdad | 22 % | 0,128 | subtipo de sancion por discriminacion no desagregado |
| Iniciativa | 6 % | 0,084 | ficha SNED de autorreporte no publica |
| Integracion | 5 % | 0,132 | ficha SNED de autorreporte no publica |
| Mejoramiento | 2 % | 0,024 | varianza del objetivo proxima a cero |

**63 % de la ponderacion esta acotada.** El campo `es_acotado` viaja en cada respuesta de la
API y se renderiza en el dashboard: la limitacion es parte del producto, no una nota al pie.

---

## 8. Deuda conocida

1. **Latencia de la explicabilidad.** SHAP exacto se valido en lote de 500 observaciones.
   Falta definir presupuesto de respuesta interactiva: precomputar y persistir en
   `ml.inferencia_atribucion`, o calcular en linea.
2. **Rutas de los notebooks.** Se movieron sin refactorizar (ver `notebooks/README.md`).
3. **Umbral de R2 por sistema.** La meta declarada es 0,60; la cumple el motor global (0,637)
   pero no el desagregado (0,583), que es el que alimenta el simulador. Corresponde declarar
   umbrales diferenciados por sistema.
4. **Persistencia de usuarios.** El directorio RBAC vive en memoria; debe migrar a `app.usuario`.
5. **Desajuste entrenamiento/servicio.** Las 8 variables `dif_simce_*` se calculan en el
   notebook de entrenamiento y no se persisten; el servicio las imputa por mediana (cobertura
   35/43 = 81,4 %). Observable vía `GET /api/v1/salud/composicion`. La solución de fondo es
   materializarlas en `hechos.indicador_anual` durante la ingesta.
6. **Versión de librería no registrada.** Los artefactos `.joblib` están acoplados a la versión
   de scikit-learn con que se entrenaron (1.5.2; fallan con 1.8). Los metadatos del registro
   deben incorporar la versión de la librería.
7. **Staging de git desde el bridge.** `git add` no puede finalizar objetos sobre la carpeta
   montada (`Operation not permitted` al liberar temporales). El repositorio esta inicializado
   y `.gitignore` verificado; el primer commit debe hacerse con git nativo en Windows.

## Modelo de clases y diagramas de secuencia

En `docs/diagramas/`, derivados del código real: arquitectura hexagonal con los cuatro puertos,
los doce patrones, y las secuencias de predicción, simulación y explicación SHAP. Fuente
Mermaid más exportación PNG.

## Limitaciones de rendimiento conocidas

| Síntoma | Causa | Estado |
|---------|-------|--------|
| Simulación en 4,6 s | 54 inferencias por llamada (9 puntos × 6 modelos); el caché no aplica porque cada punto es una observación distinta | Sin resolver |
| Ranking 2,5× más lento en PostgreSQL | `v_ranking_intra_cluster` recalcula funciones de ventana sobre 54.298 filas en cada consulta | Sin resolver |

## Normas de los planes de prueba

Los cuatro planes —maestro, integracion, aceptacion y compatibilidad de navegadores— se redactan
siguiendo **ISO/IEC/IEEE 29119**, que es la norma vigente.

Conviene ser preciso con la relacion entre ambas normas, porque es una pregunta previsible en una
defensa: **ISO/IEC/IEEE 29119-3 reemplazo formalmente a IEEE 829 en 2013**. No estan vigentes en
paralelo. Se cita 829 como antecedente por dos razones: su estructura documental —identificador,
alcance, elementos a probar, criterios de aprobacion y suspension, entregables y riesgos— se
conserva casi integra en 29119-3, y sigue siendo la referencia que se ensena.

De 29119 viene ademas lo que 829 no tenia: el proceso que produce el documento y las tecnicas de
diseno de casos —particion de equivalencia, valores limite, prueba de contrato— que aparecen en
los planes.
