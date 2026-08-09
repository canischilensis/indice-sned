# Plan de gestión del cronograma

Identificador del documento: **PGCR-SNED-01**

Define cómo se secuencia el trabajo, qué depende de qué y cómo se controla el avance. Se organiza
por **dependencias técnicas reales**, no por fechas: una fecha sin la dependencia satisfecha es
una fecha incumplida por adelantado.

---

## 1. Base de la planificación

El proyecto no se planificó por duración estimada sino por **cadena de dependencias
verificables**. La razón es específica del dominio: al inicio no se sabía qué contenían las once
fuentes públicas, y por lo tanto no se podía estimar el trabajo de modelamiento sin haber hecho
la ingesta.

Regla aplicada: **ningún incremento comienza antes de que su predecesor haya superado la
compuerta de calidad.** Un incremento sobre una base no verificada acumula el error en lugar de
avanzar.

## 2. Red de dependencias

```
 I. Ingesta y calidad (Q1)
        │
        ▼
 II. Modelamiento y explicabilidad (Q2)
        │
        ├──────────────────────────────┐
        ▼                              ▼
 III. Servicio (Q3)          V. Persistencia relacional
        │                              │
        ▼                              │
 IV. Interfaz (Q4)                     │
        │                              │
        └──────────────┬───────────────┘
                       ▼
         VI. Conmutación verificada
                       │
                       ▼
         VII. Documentación y pruebas
```

### Dependencias duras

| Incremento | No puede empezar sin | Motivo técnico |
|-----------|---------------------|----------------|
| II | I terminado | Sin matriz normalizada no hay qué entrenar |
| III | II terminado | El servicio encapsula el motor; sin puerto no hay qué encapsular |
| IV | III terminado | La interfaz consume el contrato publicado |
| V | I terminado | El esquema se deriva de la estructura real del dato ingerido |
| VI | III y V terminados | La paridad exige dos adaptadores operativos |
| VII | VI terminado | Los diagramas se derivan del código final; documentar antes es documentar un borrador |

La dependencia de VII es una decisión metodológica: los diagramas se generaron **desde el código
existente**, no como diseño previo. Documentar antes habría producido un modelo del sistema
imaginado.

## 3. Camino crítico

```
I ──▶ II ──▶ III ──▶ VI ──▶ VII
```

El incremento V (persistencia) es paralelizable respecto de III y IV, pero **converge en VI**: sin
la base cargada no hay segundo adaptador que comparar. En la práctica V se ejecutó después,
convirtiéndolo en parte del camino crítico.

El incremento IV (interfaz) **no está en el camino crítico**: podía construirse en paralelo con
V. Esto tiene una consecuencia visible en el proyecto: la interfaz quedó operativa antes de que la
base existiera, consumiendo el adaptador de archivos columnares. Esa no es una anomalía sino la
demostración de que la frontera del puerto de repositorio funcionaba desde el principio.

## 4. Hitos con criterio de cierre verificable

Cada hito cierra cuando su criterio se cumple, no cuando llega una fecha.

| Hito | Criterio de cierre | Verificación | Estado |
|------|-------------------|--------------|--------|
| H1 · Datos normalizados | Las once fuentes producen parquet con reporte de calidad y cuarentena | Reportes por fuente | Cerrado |
| H2 · Modelo entrenado y explicable | Artefactos registrados; aditividad verificada | Métricas del registro | Cerrado |
| H3 · Servicio operativo | Las trece funciones responden; control de acceso probado | Suite de integración | Cerrado |
| H4 · Interfaz operativa | Las tres ventanas contra el servicio real | Verificación manual | Cerrado |
| H5 · Base cargada y verificada | Índice reconstruido con discrepancia ≤ 0,001 | Consulta de verificación: máx. 0,0006 sobre 44.679 filas | Cerrado |
| H6 · Conmutación demostrada | Equivalencia campo por campo, todas las llamadas exitosas | 141 llamadas, 0 divergencias | Cerrado |
| H7 · Documentación completa | Requisitos, arquitectura, diseño, gestión, manuales y planes | Índice maestro en `docs/README.md` | Cerrado |
| H8 · Defensa | Sistema demostrable en vivo | — | Pendiente |

## 5. Control del avance

El avance no se mide en porcentaje declarado sino en hitos cerrados con su criterio cumplido. Un
incremento "al 80 %" no informa: o pasó la compuerta o no la pasó.

| Indicador | Valor actual |
|-----------|-------------|
| Hitos cerrados | 7 de 8 |
| Requisitos funcionales con verificación | 13 de 13 |
| Integraciones cubiertas | 5 de 5 |
| Niveles de prueba implementados | 4 de 6 |
| Documentos de línea base | Completos |

## 6. Reprogramación: los tres retrocesos del proyecto

Un cronograma honesto registra los retrocesos. Estos tres reabrieron incrementos ya cerrados y
son la evidencia más clara de que el proceso fue iterativo:

| Retroceso | Incremento reabierto | Causa | Efecto en el cronograma |
|-----------|---------------------|-------|------------------------|
| El motor desagregado no podía predecir | II | Los artefactos esperaban las banderas de ausencia; los metadatos declaraban solo las variables base | Bloqueó H3 hasta corregirse |
| La suite de paridad aprobaba sin comparar nada | VI | Tres supuestos falsos del arnés: respuestas de error, listas vacías y esquemas sin restricciones | Reabrió H6 tres veces |
| La precisión numérica truncaba los valores de origen | V | La precisión decimal elegida perdía información | Obligó a recargar la base completa |

Ninguno se resolvió relajando el criterio. Los tres se resolvieron corrigiendo la causa, que es
lo que hace que el cronograma se alargue y el resultado valga.

## 7. Riesgos de cronograma

| Riesgo | Probabilidad | Impacto | Mitigación aplicada |
|--------|-------------|---------|--------------------|
| Una fuente pública cambia de formato o desaparece | Media | Alto | Los archivos crudos se conservan localmente; la redescarga está documentada |
| Un hallazgo tardío invalida resultados reportados | Media | Alto | Verificaciones automatizadas en cada envío, para que el hallazgo llegue temprano |
| Los artefactos dejan de cargar por actualización de dependencias | Media | Alto | Versiones fijadas en el archivo de requisitos |
| El entorno de desarrollo se pierde | Baja | Alto | Todo reconstruible desde el repositorio: esquema, carga y entorno |

## 8. Restricción de calendario

El proyecto tiene una fecha de entrega fija. La estrategia frente a esa restricción no fue
comprimir el trabajo técnico sino **fijar el alcance temprano y declarar las exclusiones**, que es
lo que hace el plan de gestión del alcance.

Las dos limitaciones de rendimiento conocidas son consecuencia directa de esta decisión: se
prefirió dejarlas documentadas y verificables antes que resolverlas a costa de la documentación
o de la suite de pruebas. Es un intercambio explícito, no un descuido.
