# Plan de gestión del alcance

Identificador del documento: **PGA-SNED-01**

Define qué construye este proyecto, qué no construye y cómo se decide ante una solicitud nueva.
El valor de este plan está en la segunda parte: **un alcance que solo dice lo que sí incluye no
protege de nada**. Lo que evita la deriva es la lista de exclusiones con su justificación.

---

## 1. Enunciado del alcance

El proyecto construye un **ecosistema predictivo para el índice SNED**: un sistema que estima el
índice y sus seis factores a partir de datos públicos, explica cada estimación a nivel de
establecimiento, permite simular escenarios de gestión y expone todo ello a través de un servicio
con control de acceso y una interfaz de gestión.

El sistema **asiste** la decisión directiva. No la reemplaza, no calcula el beneficio monetario
oficial y no sustituye ningún acto administrativo.

## 2. Estructura de descomposición del trabajo

```
Ecosistema predictivo SNED
│
├── 1. Ingesta y calidad de datos (Q1)
│   ├── 1.1 Caracterización de las once fuentes públicas
│   ├── 1.2 Ingestores por formato y codificación
│   ├── 1.3 Reglas de admisión y cuarentena
│   └── 1.4 Reportes de calidad por fuente
│
├── 2. Modelamiento y explicabilidad (Q2)
│   ├── 2.1 Construcción de la matriz de entrenamiento
│   ├── 2.2 Protocolo de validación anti-fuga
│   ├── 2.3 Motor global y motor desagregado por factor
│   ├── 2.4 Atribución de Shapley con verificación de aditividad
│   ├── 2.5 Simulación de escenarios
│   └── 2.6 Registro de artefactos
│
├── 3. Servicio (Q3)
│   ├── 3.1 Interfaz de programación versionada
│   ├── 3.2 Autenticación y control de acceso por jurisdicción
│   ├── 3.3 Puerto de repositorio con dos adaptadores
│   └── 3.4 Reglas de alerta
│
├── 4. Interfaz de gestión (Q4)
│   ├── 4.1 Acceso
│   ├── 4.2 Tablero con desglose por factor y alertas
│   ├── 4.3 Simulador de escenarios
│   └── 4.4 Reporte de explicabilidad
│
├── 5. Persistencia relacional
│   ├── 5.1 Modelo entidad-relación y modelo físico
│   ├── 5.2 Esquema de 38 tablas en cuatro espacios
│   ├── 5.3 Vistas de reconstrucción y ordenamiento
│   └── 5.4 Carga idempotente y verificación del cálculo
│
└── 6. Aseguramiento y documentación
    ├── 6.1 Suite de pruebas por nivel
    ├── 6.2 Verificación de fronteras de arquitectura
    ├── 6.3 Planes de prueba
    ├── 6.4 Diagramas derivados del código
    └── 6.5 Manuales y documentación de gestión
```

## 3. Entregables

| Entregable | Estado | Ubicación |
|-----------|--------|-----------|
| Código fuente de los cuatro cuantos | Terminado | `quanta/` |
| Esquema de base de datos versionado | Terminado | `db/` |
| Base de datos cargada y verificada | Terminado | ≈ 838.000 filas |
| Artefactos de modelo con su registro | Terminado | `models/` |
| Suite de pruebas | Terminado, con tres niveles pendientes de implementar | `tests/` |
| Diagramas de arquitectura, clases y secuencia | Terminado | `docs/diagramas/` |
| Planes de prueba | Terminado | `docs/planes/` |
| Documentación de requisitos, arquitectura y diseño | Terminado | `docs/` |
| Manuales de instalación, usuario y operación | Terminado | `docs/manuales/` |
| Documento de tesis | En desarrollo | Fuera del repositorio |

## 4. Exclusiones del alcance

Cada exclusión indica su motivo. Una exclusión sin motivo se reabre en la primera conversación.

| Exclusión | Motivo | Consecuencia asumida |
|-----------|--------|---------------------|
| Reentrenamiento automatizado y orquestación de aprendizaje automático | El fenómeno es bianual; la infraestructura sería deuda técnica pura (ADR-003) | El reentrenamiento es un procedimiento manual documentado |
| Cálculo oficial del beneficio monetario | Es un acto administrativo del organismo, no un cálculo replicable | El sistema estima el índice, no el monto |
| Administración de usuarios en la aplicación | El directorio vive en memoria; el esquema está creado | No hay altas ni bajas por interfaz |
| Alta disponibilidad y replicación de la base | No existe requisito de disponibilidad establecido | Una caída de la base degrada a modo parquet |
| Aplicación móvil nativa | La interfaz es adaptable y el uso es de escritorio | — |
| Integración con sistemas de gestión escolar de terceros | Sin acceso ni requisito | — |
| Predicción del índice de años futuros sin datos de entrada | El sistema estima el índice del ciclo con las variables observadas, no proyecta el futuro | Se comunica explícitamente para evitar la lectura errónea |
| Publicación de las fichas de autorreporte | El organismo no las publica | Es el origen de la frontera de información, y es un hallazgo del proyecto |

## 5. Criterios de aceptación del alcance

El alcance se considera cubierto cuando:

1. Las once fuentes están normalizadas, con cuarentena y reporte por fuente.
2. El índice reconstruido desde la base coincide con el oficial dentro de 0,001.
3. Las trece funciones del catálogo de requisitos responden por la interfaz de programación.
4. Las tres ventanas de la interfaz operan contra el servicio real.
5. La conmutación de fuente de datos produce respuestas equivalentes, todas exitosas.
6. Las fronteras entre cuantos se verifican por máquina sin violaciones.
7. La documentación permite reconstruir el sistema desde cero en otra máquina.

Los siete están cumplidos.

## 6. Control de la deriva del alcance

Toda solicitud nueva se somete a cuatro preguntas, en orden. La primera respuesta negativa
detiene el análisis.

1. ¿Responde a un objetivo declarado del proyecto?
2. ¿Se puede verificar que quedó cumplida?
3. ¿Es compatible con las restricciones de diseño? (no inventar datos, no persistir derivadas, no
   usar el objetivo como entrada)
4. ¿Cabe en el plazo sin degradar lo ya construido?

Si el resultado es negativo pero la idea es buena, va a la lista de trabajo futuro, no al
alcance.

## 7. Trabajo futuro identificado

No forma parte del alcance. Se registra para que la exclusión sea explícita y no parezca un
olvido.

| Elemento | Valor esperado | Costo estimado |
|----------|---------------|----------------|
| Materializar las ocho variables derivadas durante la ingesta | Cobertura de 81,4 % a 100 % y fin del desajuste entrenamiento-servicio | Medio |
| Vectorizar la malla de simulación | De ≈ 4,6 s a menos de un segundo | Medio |
| Materializar la vista de ordenamiento intragrupo | Elimina el recálculo de funciones de ventana por consulta | Bajo |
| Migrar el directorio de usuarios a la base | Administración real de usuarios | Medio |
| Registrar la versión de la librería en los metadatos del artefacto | Elimina un fallo silencioso al actualizar dependencias | Bajo |
| Implementar los escenarios de aceptación | Cierra el nivel de prueba pendiente | Medio |
| Implementar la prueba de compatibilidad de navegadores | Cierra el requisito no funcional pendiente | Medio |

## 8. Supuestos y dependencias

| Supuesto | Riesgo si no se cumple |
|----------|----------------------|
| Las fuentes públicas siguen disponibles en los mismos formatos | La ingesta requiere nuevos adaptadores |
| Las ponderaciones oficiales se mantienen durante el ciclo | El catálogo cambia; el diseño ya lo contempla como dato |
| La agrupación de comparación conserva su criterio | Cambia la interpretación del ordenamiento intragrupo |
| El entorno de ejecución conserva la versión de la librería de aprendizaje | Los artefactos fallan al cargar |
