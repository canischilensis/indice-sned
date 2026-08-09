# Gestión del proyecto y metodología de desarrollo

Identificador del documento: **GP-SNED-01**

Describe el modelo de desarrollo aplicado, su correspondencia con los objetivos del proyecto y
la evidencia que deja cada incremento. El énfasis está en lo verificable: un proceso que no deja
rastro no se puede evaluar, y una metodología declarada pero no evidenciada es decoración.

---

## 1. Modelo de desarrollo adoptado

**Desarrollo incremental e iterativo con compuerta de calidad explícita por incremento.**

La elección se justifica por tres condiciones del proyecto:

| Condición | Consecuencia metodológica |
|-----------|--------------------------|
| El alcance de datos era desconocido al inicio: once fuentes públicas, formatos dispares, cobertura incierta | Un modelo en cascada habría fijado requisitos sobre datos que aún no se sabía si existían |
| El resultado tiene consecuencia monetaria | Cada incremento debe demostrar corrección antes de incorporarse, no al final |
| Un solo desarrollador | Las ceremonias de coordinación de equipo no aplican; la disciplina se traslada a compuertas automatizadas |

La consecuencia práctica es que **el control de calidad no es una fase final sino una condición
de entrada de cada incremento**. Un incremento que no supera las tres barreras no se integra:
retorna al backlog.

## 2. Estructura del trabajo: cuantos como unidades de incremento

El trabajo se organizó por cuantos de arquitectura, no por capas técnicas. Cada cuanto es una
unidad desplegable con valor demostrable por sí misma.

| Incremento | Cuanto | Resultado demostrable al cierre |
|-----------|--------|--------------------------------|
| I · Ingesta y calidad | Q1 | Once fuentes normalizadas a parquet, con cuarentena y reporte de calidad por fuente |
| II · Modelamiento y explicabilidad | Q2 | Motor dual entrenado, con atribución de Shapley verificada por aditividad |
| III · Servicio | Q3 | Interfaz de programación operativa con control de acceso por jurisdicción |
| IV · Cliente | Q4 | Tres ventanas funcionales consumiendo el servicio |
| V · Persistencia relacional | Q3 + base | Esquema de 38 tablas cargado, con el cálculo del índice auditable en SQL |
| VI · Conmutación verificada | Q3 | Dos adaptadores del mismo puerto con equivalencia demostrada campo por campo |
| VII · Documentación e instrumentación de pruebas | transversal | Planes de prueba, diagramas derivados del código y esta documentación |

Esta secuencia no es cronológica pura: los incrementos V y VI reabrieron decisiones del II y del
III. Eso es esperado en un modelo iterativo y **está documentado**, en lugar de presentarse como
un avance lineal que no ocurrió.

## 3. Correspondencia con los objetivos del proyecto

| Objetivo | Incremento que lo realiza | Evidencia |
|----------|--------------------------|-----------|
| Caracterizar y normalizar las fuentes públicas del índice | I | Reportes de calidad por fuente; parquet de cuarentena; `docs/FUENTES.md` |
| Construir un modelo capaz de estimar el índice y sus factores | II | Registro de artefactos con métricas por factor; R² documentado |
| Hacer la estimación explicable a nivel de establecimiento | II | Atribución de Shapley con verificación de aditividad |
| Exponer el modelo como servicio auditable y con control de acceso | III | Rutas con control de jurisdicción; pruebas de control de acceso |
| Entregar una interfaz de gestión utilizable por un equipo directivo | IV | Tres ventanas; incertidumbre y limitaciones visibles |
| Persistir el dominio en un modelo relacional normalizado y auditable | V | 38 tablas; el índice se reconstruye en SQL con discrepancia máxima 0,0006 |
| Demostrar que la arquitectura tolera el cambio de fuente de datos | VI | 141 llamadas, 0 divergencias |

## 4. La compuerta de incorporación

Cada incremento atraviesa tres barreras, en orden. La barrera es el mecanismo que sustituye a la
revisión por pares cuando el equipo es de una persona.

| Barrera | Qué verifica | Herramienta |
|---------|-------------|-------------|
| 1 · Código y estructura | Análisis estático, tipado, fronteras entre cuantos, esquema de base de datos, auditoría anti-fuga | `ruff`, `mypy`, `scripts/verificar_arquitectura.py`, DDL |
| 2 · Criterios de aceptación | Pruebas unitarias e integración. **Un fallo de control de acceso reprueba la barrera completa** | `pytest` |
| 3 · Umbral de precisión | El modelo candidato solo se aprueba si supera al vigente y la superioridad se sostiene con intervalos de confianza y prueba t pareada | Cuadernos de modelamiento |

Si falla cualquiera: el incremento se rechaza, retorna al backlog y se preserva la última versión
estable de los artefactos serializados.

## 5. Evidencia de aplicación de la metodología

Lo que distingue una metodología aplicada de una declarada es que la primera deja cicatrices.
Estas son verificables en el repositorio:

| Evidencia | Qué demuestra |
|-----------|---------------|
| `docs/adr/` — cinco decisiones de arquitectura registradas | Las decisiones estructurales se tomaron explícitamente, con alternativas evaluadas |
| Parquet de cuarentena por fuente | El control de calidad de datos operó de verdad, y conservó lo rechazado |
| Sección "Lo que la conmutación destapó" en el `README.md` | El incremento VI encontró defectos reales en incrementos anteriores y se dejaron documentados |
| Hallazgo de la prueba de paridad vacía, registrado en el plan de integración | Una prueba pasó tres veces sin comparar nada; el hallazgo se documentó en lugar de corregirse en silencio |
| Dos limitaciones de rendimiento declaradas y no resueltas | Se distingue entre lo resuelto y lo conocido-y-pendiente |
| Diagramas derivados del código, no del diseño previo | El modelo refleja el sistema construido |

El caso más ilustrativo es el cuarto. La suite de paridad pasó tres veces sin comparar nada:
comparaba dos respuestas de error, dos listas vacías y dos esquemas sin restricciones. El
registro de ese hallazgo vale más que su corrección, porque documenta un modo de fallo —la
prueba que se aprueba a sí misma— que reaparece en cualquier proyecto.

## 6. Gestión de la configuración

| Elemento | Estrategia |
|----------|-----------|
| Código | Control de versiones distribuido; un commit por unidad de cambio con mensaje descriptivo |
| Esquema de base de datos | Versionado como DDL en `db/`; la base se reconstruye desde el repositorio |
| Artefactos de modelo | Fuera del control de versiones por tamaño (210 MB); versionados por nombre en el registro |
| Datos crudos | Fuera del control de versiones; redescargables según `docs/FUENTES.md` |
| Configuración de despliegue | Variables de entorno; el repositorio contiene solo la plantilla |
| Contrato de ponderaciones | `contratos/catalogo_factores.json`, validado contra la base al inicializar |

## 7. Herramientas de apoyo

| Herramienta | Función en el proceso |
|-------------|----------------------|
| `pytest` con marcadores | Permite ejecutar subconjuntos: sin base de datos, sin artefactos, solo paridad |
| Integración continua | Ejecuta la suite ejecutable sin base ni artefactos en cada envío |
| `ruff`, `mypy` | Barrera 1 |
| `scripts/verificar_arquitectura.py` | **Función de aptitud atómica** (Richards y Ford, 2020, cap. 6, p. 83): convierte la regla de dependencias en una verificación objetiva que gobierna la mantenibilidad |
| Cuadernos de trabajo | Exploración y entrenamiento; no forman parte del sistema desplegado |

## 8. Riesgos gestionados durante el proyecto

| Riesgo | Materialización | Respuesta |
|--------|----------------|-----------|
| Fuga del objetivo hacia las variables de entrada | Alta | Control CTRL-02 y restricción RES-01; verificación con predictor trivial |
| Fuentes públicas incompletas o no clasificadas | Se materializó: 68,8 % de nulos estructurales | Formato largo, cuarentena, banderas de ausencia; no se rellenó |
| Acoplamiento de la versión de la librería a los artefactos | Se materializó: fallan con una versión mayor distinta | Documentado como deuda; se fija la versión en el entorno |
| Prueba que no prueba nada | Se materializó tres veces | Se añadió una prueba que verifica que las llamadas comparadas sean exitosas |
| Cambio de criterio para hacer pasar una prueba | Riesgo de proceso | Regla explícita: no se ajusta el criterio de comparación para que la prueba apruebe |

## 9. Lo que este proyecto no gestionó, y por qué

| Elemento | Motivo |
|----------|--------|
| Estimación por puntos de historia y velocidad de equipo | Un solo desarrollador; la métrica no tendría con qué compararse |
| Ceremonias de coordinación | Sin equipo que coordinar |
| Gestión de proveedores | Sin dependencias contractuales externas |
| Orquestación de aprendizaje automático en producción | ADR-003: el fenómeno es bianual; la infraestructura sería deuda pura |
