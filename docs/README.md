# Documentación del proyecto `indice-sned`

Índice maestro. Cada documento tiene un identificador y una función; la última sección mapea todo
al índice del Capítulo IV de la tesis.

---

## Mapa rápido

| Si busca… | Vaya a |
|-----------|--------|
| Levantar el sistema desde cero | `manuales/MANUAL_INSTALACION.md` |
| Entender la arquitectura | `arquitectura/ARQUITECTURA_AD_HOC.md` y `ARCHITECTURE.md` |
| Saber qué hace cada clase | `diseno/DISENO_DEL_SOFTWARE.md` |
| Entender la base de datos | `diseno/DISENO_BASE_DATOS.md` y `db/README.md` |
| Saber qué no se puede tocar | `gestion/PLAN_GESTION_CAMBIOS.md`, sección 3 |
| Usar el sistema | `manuales/MANUAL_USUARIO.md` |
| Saber qué se probó y cómo | `planes/PLAN_PRUEBAS.md` |
| Ver de dónde sale cada requisito | `requisitos/MATRIZ_TRAZABILIDAD.md` |

---

## 1. Requisitos

| Documento | ID | Contenido |
|-----------|-----|-----------|
| `requisitos/CATALOGO_REQUISITOS.md` | CR-SNED-01 | 13 requisitos funcionales, 12 no funcionales, 6 restricciones de diseño y el alcance excluido |
| `requisitos/CASOS_DE_USO.md` | CU-SNED-01 | 12 casos de uso con descripción completa, flujos alternativos y realización en código |
| `requisitos/MATRIZ_TRAZABILIDAD.md` | MT-SNED-01 | Requisito → caso de uso → componente → código → prueba, en ambas direcciones |
| `CUESTIONARIO_REQUISITOS.md` | — | Cuestionario de levantamiento, origen de los requisitos |

## 2. Arquitectura

| Documento | ID | Contenido |
|-----------|-----|-----------|
| `arquitectura/ARQUITECTURA_AD_HOC.md` | AR-SNED-01 | La arquitectura hexagonal por cuantos, y **dónde se observa en cada artefacto UML** |
| `arquitectura/VISTAS_4MAS1.md` | V41-SNED-01 | Las cinco vistas de Kruchten: lógica, procesos, desarrollo, física y escenarios |
| `arquitectura/PLATAFORMA_DE_OPERACION.md` | PO-SNED-01 | Despliegue con servidores separados de datos y aplicación, dimensionamiento y contingencia |
| `ARCHITECTURE.md` | — | Documento vivo: motores de la arquitectura, decisiones y deuda conocida |
| `PATRONES_DE_DISENO.md` | — | 12 patrones aplicados y 12 descartados, con fuentes citadas |
| `adr/` | ADR-001 a 007 | Decisiones de arquitectura registradas |
| `agente/AGENTE_ASESOR.md` | AG-SNED-01 | El cuanto 5: puerto, guardarraíles, proveedores, evaluación y defectos encontrados por el uso |
| `agente/COMPARACION_ORQUESTADORES.md` | CO-SNED-01 | Comparación medida entre el bucle propio y el ReAct de LangGraph, sobre los mismos veinte casos |
| `agente/COMPARACION_PROVEEDORES.md` | CP-SNED-01 | Comparación medida entre el adaptador determinista y un modelo local de 8B, sobre los mismos veinte casos |
| `agente/evidencia/` | — | Salida completa de las corridas que sustentan las comparaciones, caso por caso |

## 3. Diseño

| Documento | ID | Contenido |
|-----------|-----|-----------|
| `diseno/DISENO_DEL_SOFTWARE.md` | DS-SNED-01 | Modelo de clases por cuanto, responsabilidades y deuda de diseño |
| `diseno/DISENO_BASE_DATOS.md` | DB-SNED-01 | 38 tablas, seis decisiones de normalización, precisión numérica y verificación del cálculo |
| `diseno/MOCKUPS_Y_PANTALLAS.md` | UI-SNED-01 | Maquetas de las cuatro pantallas y procedimiento de captura |
| `diagramas/` | — | 7 imágenes y 5 fuentes Mermaid, derivadas del código |
| `Anexo_mapeo_conceptual_fisico.docx` | — | Reglas de transformación de modelo conceptual a físico |

## 4. Gestión del proyecto

| Documento | ID | Contenido |
|-----------|-----|-----------|
| `gestion/METODOLOGIA_Y_GESTION.md` | GP-SNED-01 | Modelo de desarrollo, incrementos, compuerta de calidad y evidencia de aplicación |
| `gestion/PLAN_CALIDAD.md` | PGC-SNED-01 | Modelo de calidad con métricas y umbrales; calidad del dato y del modelo |
| `gestion/PLAN_GESTION_CAMBIOS.md` | PGCA-SNED-01 | Elementos bajo control, cambios prohibidos y registro de los ya aplicados |
| `gestion/PLAN_COMUNICACIONES.md` | PCO-SNED-01 | Interesados, canales y **la interfaz como canal formal** |
| `gestion/PLAN_GESTION_ALCANCE.md` | PGA-SNED-01 | Descomposición del trabajo, exclusiones justificadas y trabajo futuro |
| `gestion/PLAN_GESTION_CRONOGRAMA.md` | PGCR-SNED-01 | Red de dependencias, hitos con criterio verificable y los tres retrocesos |

## 5. Pruebas

| Documento | ID | Estado |
|-----------|-----|--------|
| `planes/PLAN_PRUEBAS.md` | PPM-SNED-01 | Plan maestro |
| `planes/PLAN_INTEGRACION.md` | PPI-SNED-01 | 5 de 5 integraciones cubiertas |
| `planes/PLAN_ACEPTACION.md` | PPA-SNED-01 | Escenarios redactados, sin implementar |
| `planes/PLAN_COMPATIBILIDAD.md` | PPC-SNED-01 | Sin implementar |

## 6. Manuales y operación

| Documento | ID | Contenido |
|-----------|-----|-----------|
| `manuales/MANUAL_INSTALACION.md` | MI-SNED-01 | Instalación completa desde cero, con verificación por paso |
| `manuales/MANUAL_USUARIO.md` | MU-SNED-01 | Uso de las cuatro ventanas y **cómo interpretar lo que muestran** |
| `manuales/MANUAL_MONITORIZACION.md` | MM-SNED-01 | Tres capas: disponibilidad, integridad del dato y validez del modelo |
| `manuales/PROCEDIMIENTOS_OPERATIVOS.md` | PR-SNED-01 | Nueve procedimientos, de PR-01 a PR-09 |
| `FUENTES.md` | — | Origen y redescarga de los datos públicos |

---

## 7. Correspondencia con el índice del Capítulo IV

| Punto del índice | Documento que lo cubre |
|------------------|------------------------|
| Gestión de proyecto: metodología, objetivos y cronograma | `gestion/METODOLOGIA_Y_GESTION.md` + `gestion/PLAN_GESTION_CRONOGRAMA.md` |
| Diseño de los componentes funcionales, con artefactos UML | `requisitos/CASOS_DE_USO.md` + `diagramas/` (secuencia) + `diseno/DISENO_DEL_SOFTWARE.md` |
| Matriz de trazabilidad de requerimientos | `requisitos/MATRIZ_TRAZABILIDAD.md` |
| Arquitectura de software a implementar | `arquitectura/ARQUITECTURA_AD_HOC.md` (sección 2: dónde se ve en cada artefacto UML) |
| Plan de Calidad | `gestion/PLAN_CALIDAD.md` |
| Plan de Gestión de Cambios | `gestion/PLAN_GESTION_CAMBIOS.md` |
| Plan de Comunicaciones | `gestion/PLAN_COMUNICACIONES.md` |
| Plan de Gestión de Alcance | `gestion/PLAN_GESTION_ALCANCE.md` |
| Plan de Gestión del Cronograma | `gestion/PLAN_GESTION_CRONOGRAMA.md` |
| Plan de Pruebas | `planes/PLAN_PRUEBAS.md` y los tres planes específicos |
| Componentes del Modelo 4+1 | `arquitectura/VISTAS_4MAS1.md` |
| Modelo de base de datos y de clases | `diseno/DISENO_BASE_DATOS.md` + `diseno/DISENO_DEL_SOFTWARE.md` + `diagramas/` |
| Diseño del software | `diseno/DISENO_DEL_SOFTWARE.md` |
| Diseño de la base de datos | `diseno/DISENO_BASE_DATOS.md` + `db/README.md` |
| Diseño de la plataforma de operación | `arquitectura/PLATAFORMA_DE_OPERACION.md` |
| Mockups y pantallazos del sistema | `diseno/MOCKUPS_Y_PANTALLAS.md` |
| Procedimientos operativos | `manuales/PROCEDIMIENTOS_OPERATIVOS.md` |
| Manual de usuario | `manuales/MANUAL_USUARIO.md` |
| Manual de instalación | `manuales/MANUAL_INSTALACION.md` |
| Manual de monitorización | `manuales/MANUAL_MONITORIZACION.md` |
| Planes de pruebas | `planes/` |

---

## 8. Estado del sistema

| Indicador | Valor |
|-----------|-------|
| Tablas en la base | 38 en cuatro espacios de nombres |
| Filas cargadas | ≈ 838.000 |
| Discrepancia del índice reconstruido | máx. 0,0006 sobre 44.679 filas |
| Pruebas en la suite | 61 |
| Llamadas comparadas entre adaptadores | 141, con 0 divergencias |
| Cobertura de variables del modelo | 81,4 % (35 de 43) |
| Requisitos funcionales con verificación | 13 de 13 |
| Niveles de prueba implementados | 4 de 6 |
| Ponderación acotada por información no publicada | 63 % |

## 9. Lo que está declarado como pendiente

No es una lista de olvidos: cada elemento está documentado con su causa en el documento
correspondiente.

| Pendiente | Documento donde se detalla |
|-----------|---------------------------|
| Simulación en ≈ 4,6 s | `arquitectura/VISTAS_4MAS1.md`, vista de procesos |
| Ordenamiento intragrupo 2,5× más lento en la base relacional | ídem |
| Ocho variables derivadas no persistidas: cobertura 81,4 % | `diseno/DISENO_DEL_SOFTWARE.md`, deuda 2 |
| Directorio de usuarios en memoria | `diseno/DISENO_DEL_SOFTWARE.md`, deuda 1 |
| Versión de librería no registrada en los metadatos | `diseno/DISENO_DEL_SOFTWARE.md`, deuda 3 |
| Escenarios de aceptación sin implementar | `planes/PLAN_ACEPTACION.md` |
| Compatibilidad de navegadores sin implementar | `planes/PLAN_COMPATIBILIDAD.md` |
| Motor desagregado bajo el umbral de R² declarado | `gestion/PLAN_CALIDAD.md`, sección 4 |
