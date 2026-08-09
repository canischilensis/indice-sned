# Plan maestro de pruebas

Identificador del documento: **PPM-SNED-01**
Norma de referencia: **ISO/IEC/IEEE 29119**, que es la vigente. Se cita **IEEE 829** como
antecedente: 29119-3 lo reemplazó formalmente en 2013, y conserva casi íntegra su estructura
documental —identificador, alcance, elementos a probar, criterios de aprobación y suspensión,
entregables y riesgos—. De 29119 viene además lo que 829 no tenía: el proceso que produce el
documento y las técnicas de diseño de casos.

Este documento es el plan de nivel superior. Los tres planes específicos —integración, aceptación
y compatibilidad— cuelgan de él.

---

## 1. Alcance

**Se prueba:** los cuatro cuantos, sus fronteras, el contrato publicado de la interfaz de
programación, el control de acceso, la equivalencia entre los adaptadores del puerto de datos y la
reconstrucción del índice desde el dato persistido.

**No se prueba:** el desempeño bajo carga concurrente, la seguridad frente a ataque dirigido y la
accesibilidad. Las tres exclusiones están declaradas en el plan de calidad con su motivo.

## 2. Estrategia

La estrategia se resume en una frase: **una prueba debe poder fallar**. El proyecto ya encontró
tres pruebas que aprobaban sin comparar nada, y ese hallazgo determinó la estrategia:

| Principio | Consecuencia práctica |
|-----------|----------------------|
| Toda comparación verifica primero que haya algo que comparar | La suite de paridad incluye una prueba que exige que todas las llamadas comparadas sean exitosas |
| Un esquema sin restricciones no valida nada | La prueba de contrato exige que las rutas del cliente declaren su tipo de respuesta, y comprueba que el validador rechaza un cuerpo inválido |
| Un conjunto vacío no es equivalencia | El arnés de comparación usa un perfil con jurisdicción real sobre la muestra |
| El criterio no se mueve para que la prueba apruebe | Si la comparación falla, se investiga la causa |

## 3. Niveles de prueba

| Nivel | Qué verifica | Ubicación | Estado |
|-------|-------------|-----------|--------|
| **Unitario** | Una clase o función aislada, con dobles | `tests/unitarias/` | Implementado |
| **Integración** | Dos componentes reales a través de su frontera | `tests/integracion/` | Implementado — PPI-SNED-01 |
| **Paridad** | Dos implementaciones del mismo puerto | `tests/paridad/` | Implementado |
| **Arquitectura** | Reglas estructurales verificadas por máquina | `tests/arquitectura/` | Implementado |
| **Aceptación** | Escenario de negocio completo, en lenguaje del usuario | `tests/aceptacion/` | **Escenarios redactados, sin implementar** — PPA-SNED-01 |
| **Compatibilidad** | La interfaz sobre distintos motores de navegador | `tests/compatibilidad/` | **Sin implementar** — PPC-SNED-01 |

### Organización

Híbrida: **por tipo en el primer nivel, por cuanto adentro**. Refleja la nomenclatura que exige la
tesis y conserva la trazabilidad al cuanto.

```
tests/
├── unitarias/
│   ├── compartido/   el mecanismo componible de especificaciones
│   ├── q1/           reglas de cuarentena y esqueleto de ingesta
│   ├── q2/           contrato del índice, decoradores, constructor, proxy, fábrica
│   └── q3/           repositorio con adaptadores y reglas de alerta
├── integracion/
│   ├── q1/           pipeline de calidad extremo a extremo
│   └── q3/           interfaz de programación, control de acceso y contrato publicado
├── aceptacion/       pendiente
├── compatibilidad/   pendiente
├── arquitectura/     fronteras de cuantos ejecutables
└── paridad/          los dos adaptadores del mismo puerto
```

## 4. Marcadores y ejecución selectiva

Declarados en `pyproject.toml`:

| Marcador | Selecciona |
|----------|-----------|
| `datos` | Pruebas sobre el pipeline de datos |
| `modelo` | Pruebas estadísticas sobre el motor predictivo |
| `api` | Pruebas sobre el servicio y el control de acceso |
| `paridad` | Equivalencia entre adaptadores |
| `requiere_datos` | Necesita los archivos columnares o el registro de artefactos |
| `requiere_bd` | Necesita PostgreSQL levantado |

```bash
pytest                          # la suite completa: 61 pruebas
pytest tests/unitarias          # solo unitarias
pytest -m paridad               # solo paridad: sin base ni artefactos
pytest -m "not requiere_bd"     # omitir lo que exige PostgreSQL
pytest -m "not requiere_datos"  # lo que corre en integración continua
```

Los dos últimos marcadores son los que permiten que la suite corra en integración continua sin
datos ni artefactos, que no se versionan por tamaño.

## 5. Técnicas de diseño de casos aplicadas

De ISO/IEC/IEEE 29119-4:

| Técnica | Dónde se aplica |
|---------|----------------|
| Prueba de contrato | La respuesta se valida contra el esquema publicado |
| Partición de equivalencia | Identificador existente, inexistente, no numérico |
| Análisis de valores límite | Establecimiento sin medición de segundo medio; con los seis factores; con factores ausentes |
| Prueba comparativa | Las mismas llamadas contra ambos adaptadores, campo por campo |
| Prueba basada en reglas | Cada regla de alerta contra su umbral, por encima y por debajo |
| Verificación de invariantes | Aditividad de la explicación; suma de ponderaciones; una fila por establecimiento en el listado |

## 6. Criterios de aprobación y de suspensión

**Aprobación de la suite:**

1. Todas las pruebas de la selección aplicable pasan.
2. La paridad informa cero divergencias **y** todas las llamadas comparadas son exitosas.
3. La verificación de fronteras de cuantos no reporta violaciones.
4. La verificación del cálculo del índice da discrepancia ≤ 0,001.

**Suspensión.** La ejecución se detiene y no se reanuda hasta resolver la causa cuando:

- Falla una prueba de control de acceso. Es la única categoría que reprueba la barrera completa.
- La cobertura de composición informa cero: el servicio no está leyendo la fuente y toda
  comparación posterior sería sobre vacío.
- La discrepancia del índice supera 0,001: hay un problema de precisión y las estimaciones
  construidas encima no son válidas.

## 7. Entorno de prueba

| Nivel | Requiere base | Requiere artefactos | Corre en integración continua |
|-------|--------------|--------------------|-----------------------------|
| Unitario | No | No, usa dobles | Sí |
| Integración Q1 | No | No | Sí |
| Integración Q3 | Sí | Sí, una prueba | Parcial |
| Paridad | No | No | **Sí** |
| Arquitectura | No | No | Sí |

Que la paridad corra sin base ni artefactos es deliberado: usa respuestas capturadas previamente
como línea base. Es la propiedad que la hace ejecutable en cada envío.

## 8. Datos de prueba

| Conjunto | Origen | Uso |
|----------|--------|-----|
| Muestra de veinte establecimientos | Extraída del conjunto depurado | Comparación entre adaptadores |
| Línea base de respuestas del adaptador columnar | Capturada antes de la conmutación | Referencia de la comparación |
| Dobles de estrategia predictiva | Construidos en las pruebas | Aislamiento de las unitarias |
| Perfiles de demostración | Directorio en memoria | Control de acceso |

**Nota sobre el perfil de comparación:** el arnés registra un perfil propio con jurisdicción sobre
los veinte identificadores de la muestra. Antes usaba el perfil de auditoría, cuya lista de
jurisdicción está vacía, y por eso el listado comparaba dos conjuntos vacíos y aprobaba.

## 9. Riesgos de la actividad de prueba

| Riesgo | Estado | Mitigación |
|--------|--------|-----------|
| Prueba que aprueba sin verificar nada | **Se materializó tres veces** | Prueba explícita de que todas las llamadas son exitosas; validación del validador |
| Artefactos no versionados | Permanente | Dobles en unitarias; una sola prueba carga un artefacto real |
| Datos no versionados | Permanente | Marcadores de exclusión; línea base capturada para la paridad |
| Acoplamiento a la versión de la librería | Permanente | Versiones fijadas en el archivo de requisitos |
| Diferencias legítimas entre adaptadores tomadas por defectos | Gestionado | Lista explícita de campos excluidos por diseño, con su motivo |

## 10. Entregables

| Entregable | Ubicación |
|-----------|-----------|
| Este plan maestro | `docs/planes/PLAN_PRUEBAS.md` |
| Plan de integración PPI-SNED-01 | `docs/planes/PLAN_INTEGRACION.md` |
| Plan de aceptación PPA-SNED-01 | `docs/planes/PLAN_ACEPTACION.md` |
| Plan de compatibilidad PPC-SNED-01 | `docs/planes/PLAN_COMPATIBILIDAD.md` |
| Suite ejecutable | `tests/` |
| Línea base y resultado de la comparación | `tests/paridad/baseline_parquet/`, `tests/paridad/resultado_postgres/` |
| Matriz de trazabilidad | `docs/requisitos/MATRIZ_TRAZABILIDAD.md` |

## 11. Estado consolidado

| Indicador | Valor |
|-----------|-------|
| Pruebas en la suite | 61 |
| Integraciones cubiertas | 5 de 5 |
| Llamadas comparadas entre adaptadores | 141 |
| Divergencias | 0 |
| Niveles implementados | 4 de 6 |
| Requisitos funcionales con verificación asociada | 13 de 13 |
