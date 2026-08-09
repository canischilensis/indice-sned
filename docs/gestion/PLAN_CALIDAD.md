# Plan de gestión de la calidad

Identificador del documento: **PGC-SNED-01**
Marco de referencia: ISO/IEC 25010 para el modelo de calidad del producto; ISO/IEC/IEEE 29119
para el proceso de prueba.

Este plan define qué significa "de calidad" en este proyecto de forma que pueda comprobarse. Un
atributo de calidad sin métrica y sin umbral es una aspiración; aquí cada uno tiene ambos.

---

## 1. Política de calidad

Tres reglas gobiernan todas las decisiones de este plan:

1. **La calidad se verifica, no se declara.** Todo atributo tiene un mecanismo automatizado o un
   procedimiento documentado que lo comprueba.
2. **No se ajusta el criterio para que la prueba apruebe.** Si una comparación falla, se
   investiga la causa; el umbral no se mueve para acomodar el resultado.
3. **Lo que no se cumple se declara.** Un defecto conocido y documentado es un estado aceptable
   del proyecto. Un defecto conocido y silenciado, no.

## 2. Modelo de calidad del producto

Características de ISO/IEC 25010 aplicables, con su medida en este sistema:

| Característica | Subcaracterística priorizada | Métrica | Umbral | Estado |
|----------------|------------------------------|---------|--------|--------|
| Adecuación funcional | Corrección funcional | Discrepancia entre el índice reconstruido y el oficial | ≤ 0,001 | **Cumple**: máx. 0,0006 |
| Adecuación funcional | Completitud funcional | Requisitos funcionales con verificación asociada | 100 % | Cumple: 13 de 13 |
| Eficiencia de desempeño | Comportamiento temporal | Latencia de las operaciones de lectura | < 1 s | Cumple, con dos excepciones declaradas |
| Compatibilidad | Interoperabilidad | Conformidad de las respuestas con el esquema publicado | 100 % de las rutas del cliente | Cumple |
| Usabilidad | Protección frente a errores del usuario | El usuario no puede pedir un establecimiento fuera de su jurisdicción | Sin campo libre en la interfaz | Cumple |
| Fiabilidad | Madurez | Suite verde en cada envío | 100 % | Cumple |
| Fiabilidad | Recuperabilidad | La base se reconstruye desde el repositorio | Procedimiento documentado | Cumple |
| Seguridad | Confidencialidad | Accesos fuera de jurisdicción | 0 | Cumple |
| Mantenibilidad | Modularidad | Violaciones del grafo de dependencias entre cuantos | 0 | Cumple, verificado por máquina |
| Mantenibilidad | Capacidad de ser probado | Suite ejecutable sin base de datos ni artefactos | Sí | Cumple |
| Portabilidad | Adaptabilidad | Adaptadores intercambiables del puerto de datos | ≥ 2, con equivalencia demostrada | Cumple: 141 llamadas, 0 divergencias |

## 3. Calidad del dato

Es una dimensión aparte porque el sistema estima sobre datos públicos incompletos, y la calidad
del dato condiciona todo lo demás.

| Dimensión | Regla | Mecanismo | Umbral |
|-----------|-------|-----------|--------|
| Integridad referencial | Ningún hecho apunta a un establecimiento inexistente | Claves foráneas + cuarentena en ingesta | 0 huérfanos persistidos |
| Unicidad | Una medición por combinación de llave | Llaves primarias compuestas | 0 duplicados |
| Completitud | La ausencia se declara, no se rellena | Formato largo + banderas de ausencia | 68,8 % de nulos estructurales, declarados |
| Cobertura de llave | Proporción de registros con identificador válido | `ReporteCalidad.cobertura_llave` | ≥ 0,95, y si no se alcanza, se reporta |
| Precisión numérica | El viaje de ida y vuelta contra el archivo de origen no pierde información | Precisión decimal medida por columna | Diferencia 0 |
| Vigencia temporal | Ningún dato posterior a la fecha de corte entra al entrenamiento | Ventana declarada en el esquema | CTRL-02 |

**Regla de oro del dato, no negociable:** si una fuente no cubre un establecimiento, esa fila no
existe. No se imputan filas para que los conteos cuadren. La ausencia es un hallazgo sobre la
publicación estatal, no un defecto a maquillar.

## 4. Calidad del modelo predictivo

| Métrica | Motor global | Motor desagregado | Umbral declarado |
|---------|-------------|-------------------|------------------|
| R² sobre partición de prueba | 0,637 | 0,583 | 0,60 |
| Verificación anti-fuga | R² del predictor trivial ≈ 0 | ídem | Obligatoria |
| Aditividad de la explicación | — | Verificada, tolerancia 1e-3 | Obligatoria |

**Incumplimiento declarado:** el motor desagregado no alcanza el umbral de 0,60 y es el que
alimenta el simulador. Corresponde declarar umbrales diferenciados por sistema, porque los dos
motores no responden la misma pregunta: uno estima mejor, el otro dice qué mover. Se deja como
incumplimiento visible en lugar de rebajar la meta.

## 5. Actividades de aseguramiento

| Actividad | Cuándo | Responsable | Salida |
|-----------|--------|-------------|--------|
| Análisis estático y de tipos | Cada cambio | Desarrollador | Salida de `ruff` y `mypy` |
| Verificación de fronteras de cuantos | Cada cambio | Automatizada | Código de retorno del script |
| Suite de pruebas | Cada envío | Integración continua | Reporte de `pytest` |
| Prueba de paridad entre adaptadores | Cada envío | Integración continua | Resumen con conteo de divergencias |
| Verificación del cálculo del índice en SQL | Tras cada carga | Desarrollador | Discrepancia máxima, media y filas comparadas |
| Revisión de deriva de datos | Por ciclo bianual | Desarrollador | Registro de contraste contra la línea base |
| Prueba de compatibilidad de navegadores | Antes de cada entrega | Desarrollador | Matriz de PPC-SNED-01 |

## 6. Niveles de prueba

Detalle completo en `docs/planes/PLAN_PRUEBAS.md`.

| Nivel | Alcance | Ubicación | Marcador |
|-------|---------|-----------|----------|
| Unitario | Una clase o función, con dobles | `tests/unitarias/` | por cuanto |
| Integración | Dos componentes reales a través de su frontera | `tests/integracion/` | `datos`, `api` |
| Paridad | Dos implementaciones del mismo puerto | `tests/paridad/` | `paridad` |
| Arquitectura | Reglas estructurales | `tests/arquitectura/` | — |
| Aceptación | Escenario de negocio completo | `tests/aceptacion/` | pendiente |
| Compatibilidad | Interfaz sobre distintos motores de navegador | `tests/compatibilidad/` | pendiente |

## 7. Criterios de entrada y salida

**Criterio de entrada a la fase de prueba de un incremento:** el código compila, el análisis
estático pasa y las fronteras de cuantos se respetan.

**Criterio de salida (Definición de Terminado):**

1. Barrera 1 superada: estático, tipos, esquema, anti-fuga.
2. Barrera 2 superada: pruebas unitarias y de integración en verde. Un fallo de control de
   acceso reprueba la barrera completa.
3. Barrera 3 superada, si el incremento toca el modelo: superioridad estadísticamente sostenida.
4. La documentación afectada está actualizada en el mismo cambio.
5. Los defectos conocidos que quedan abiertos están registrados con su causa.

## 8. Métricas de seguimiento

| Métrica | Valor actual | Fuente |
|---------|-------------|--------|
| Pruebas en la suite | 61 | `pytest` |
| Llamadas comparadas en paridad | 141 | Resumen de paridad |
| Divergencias entre adaptadores | 0 | Resumen de paridad |
| Cobertura de variables del modelo en la fuente activa | 81,4 % (35 de 43) | `GET /api/v1/salud/composicion` |
| Filas comparadas en la verificación del índice | 44.679 | Consulta de verificación |
| Violaciones del grafo de dependencias | 0 | Script de verificación |
| Requisitos sin cobertura automatizada | 3, declarados | `MATRIZ_TRAZABILIDAD.md` |

## 9. Defectos: clasificación y tratamiento

| Severidad | Definición | Tratamiento |
|-----------|-----------|-------------|
| Crítica | Acceso fuera de jurisdicción, cálculo del índice incorrecto, pérdida de dato | Bloquea la entrega; se corrige antes de cualquier otro trabajo |
| Alta | Una ruta responde error donde debía responder dato; divergencia entre adaptadores | Bloquea el incremento |
| Media | Degradación de rendimiento sobre el umbral; error de etiqueta visible al usuario | Se registra y se planifica |
| Baja | Cosmética, redacción, formato | Se agrupa |

**Defectos abiertos declarados:**

| Defecto | Severidad | Estado |
|---------|-----------|--------|
| Simulación en ≈ 4,6 s | Media | Abierto por decisión: la solución exige vectorizar la malla |
| Ordenamiento intragrupo 2,5× más lento en la base relacional | Media | Abierto por decisión: la solución exige materializar la vista |
| Motor desagregado bajo el umbral de R² | Media | Abierto: corresponde declarar umbrales por sistema |
| Directorio de usuarios en memoria | Media | Abierto: migración a `app.usuario` pendiente |
| Versión de librería no registrada en los metadatos | Media | Abierto |

## 10. Lo que este plan no cubre

| Elemento | Motivo |
|----------|--------|
| Pruebas de carga y concurrencia | El sistema atiende a equipos directivos, no a tráfico masivo; el requisito de concurrencia no está establecido |
| Pruebas de penetración | Fuera del alcance del proyecto de título |
| Auditoría de accesibilidad | Reconocido como brecha; no hay requisito formal establecido |
