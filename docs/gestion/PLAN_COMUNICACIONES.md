# Plan de gestión de las comunicaciones

Identificador del documento: **PCO-SNED-01**

Define quién necesita saber qué, con qué frecuencia y en qué formato. En un proyecto de un solo
desarrollador la comunicación relevante no es de coordinación interna sino **hacia afuera**:
hacia el profesor guía, hacia la comisión evaluadora y, sobre todo, hacia el usuario final a
través del propio producto.

Ese último canal es el que suele olvidarse. La interfaz también comunica, y este plan lo trata
como un canal formal con requisitos verificables.

---

## 1. Interesados

| Interesado | Interés principal | Qué necesita recibir | Frecuencia |
|-----------|-------------------|---------------------|------------|
| Profesor guía | Avance verificable y decisiones fundamentadas | Estado del incremento, decisiones tomadas, obstáculos | Por hito |
| Comisión evaluadora | Que el sistema exista, funcione y esté justificado | Documento de tesis, demostración funcional, documentación técnica | En la defensa |
| Equipo directivo (usuario final) | Qué mover para mejorar el índice, y cuánto confiar en la estimación | Estimación con incertidumbre, alertas, explicación, limitaciones | En cada uso |
| Sostenedor | Situación comparada de su red | Listado, posición dentro del grupo | En cada uso |
| Auditor | Que el cálculo sea verificable | Catálogo de ponderaciones, cobertura, vista de reconstrucción | Bajo demanda |
| Desarrollador futuro | Poder retomar el sistema sin arqueología | Documentación de arquitectura, decisiones registradas, manuales | Permanente |

## 2. Canales

| Canal | Contenido | Interesado | Formato |
|-------|-----------|-----------|---------|
| Repositorio de código | Fuente, esquema, pruebas | Desarrollador futuro | Control de versiones |
| `docs/` | Arquitectura, requisitos, diseño, planes, manuales | Guía, comisión, desarrollador futuro | Markdown versionado |
| `docs/adr/` | Decisiones de arquitectura con alternativas evaluadas | Guía, comisión | Registro por decisión |
| Documentación interactiva del servicio | Contrato vivo de cada ruta | Desarrollador integrador | Generada desde el código |
| **La interfaz de usuario** | Estimación, incertidumbre, alertas, limitaciones | Directivo, sostenedor | Producto |
| Reportes de calidad de ingesta | Cobertura y registros en cuarentena por fuente | Auditor, desarrollador | Archivo por ejecución |
| Documento de tesis | Marco, metodología, resultados y discusión | Comisión | Documento formal |

## 3. La interfaz como canal de comunicación

Requisitos de comunicación que el producto debe cumplir. No son sugerencias de estilo: son
condiciones para que la estimación no induzca a error.

| Requisito | Cómo se cumple | Dónde |
|-----------|----------------|-------|
| La incertidumbre acompaña siempre a la estimación | El error medio se muestra junto al índice, en la misma tarjeta | Tablero |
| Lo acotado por información no publicada se distingue | Color diferenciado en el gráfico y columna de restricción en la tabla | Tablero |
| El alcance del sistema se declara en pantalla | Aviso al pie de cada vista | Las tres vistas |
| La posición real se distingue de lo simulado | Punto de referencia sobre la curva | Simulador |
| La explicación declara si es válida | Tarjeta de verificación de aditividad | Reporte de explicabilidad |
| La ausencia de dato se nombra | "Sin medición de …" en lugar de un cero | Reporte de explicabilidad |
| El error se muestra tal cual | El mensaje del servicio se presenta sin suavizar | Todas |

El último punto tiene una consecuencia visible: si se consulta un establecimiento que no está en
la base analítica, la interfaz dice exactamente eso. **Es comunicación correcta**, no un fallo de
usabilidad.

## 4. Comunicación de limitaciones

El sistema estima con información incompleta. Ocultarlo sería el peor defecto posible, porque el
índice tiene consecuencia monetaria y un directivo podría tomar decisiones sobre una estimación
que el sistema sabe frágil.

| Limitación | Cómo se comunica | Destinatario |
|-----------|------------------|--------------|
| El 63 % de la ponderación está acotada por información no publicada | Campo en cada respuesta, color en el gráfico, alerta informativa dedicada | Directivo |
| El motor desagregado tiene menor poder explicativo que el global | Documentado; el motor activo se muestra en el tablero | Directivo, comisión |
| La cobertura de variables es 81,4 % | Ruta de composición y diagnóstico | Auditor |
| La simulación tarda unos 4,6 s | Estado de carga explícito; documentado como limitación conocida | Directivo, comisión |
| El ordenamiento intragrupo es más lento en la base relacional | Documentado | Comisión, desarrollador futuro |

## 5. Comunicación de incidencias

| Tipo de incidencia | Se comunica a | Vehículo | Plazo |
|-------------------|---------------|----------|-------|
| Fallo que impide operar | Guía | Directo | Inmediato |
| Hallazgo que invalida un resultado reportado | Guía | Directo, con la evaluación de impacto | Antes de continuar |
| Defecto conocido que no se corregirá | Comisión | Documentación, sección de deuda | En la entrega |
| Error de dato en la fuente pública | Documentación | `docs/FUENTES.md` y reporte de calidad | En la ejecución |

La segunda fila es la importante. Este proyecto ya la ejerció: la prueba de paridad que aprobaba
sin comparar nada se comunicó como hallazgo, con su causa y su corrección, en lugar de arreglarse
en silencio. Un hallazgo así, comunicado, es evidencia de rigor; el mismo hallazgo, silenciado,
es lo contrario.

## 6. Documentación como comunicación diferida

El desarrollador futuro no puede preguntar. Toda pregunta previsible debe estar respondida por
escrito.

| Pregunta previsible | Documento que la responde |
|--------------------|--------------------------|
| ¿Por qué está partido en cuatro cuantos? | `docs/adr/ADR-001` |
| ¿Por qué hay dos motores predictivos? | `docs/adr/ADR-004` |
| ¿Por qué no hay orquestación de aprendizaje automático? | `docs/adr/ADR-003` |
| ¿Por qué las ponderaciones son dato y no constantes? | `docs/adr/ADR-005` |
| ¿Por qué existe el adaptador de parquet si ya hay base de datos? | `docs/arquitectura/PLATAFORMA_DE_OPERACION.md`, sección de contingencia |
| ¿Por qué esta tabla tiene seis decimales? | `docs/diseno/DISENO_BASE_DATOS.md` |
| ¿Cómo levanto todo desde cero? | `docs/manuales/MANUAL_INSTALACION.md` |
| ¿Qué pasa si una prueba falla? | `docs/planes/PLAN_PRUEBAS.md` |
| ¿Qué no debo tocar? | `docs/gestion/PLAN_GESTION_CAMBIOS.md`, sección 3 |

## 7. Calendario de comunicación

| Momento | Contenido | Destinatario |
|---------|-----------|--------------|
| Cierre de cada incremento | Qué quedó terminado, qué se descubrió, qué queda abierto | Guía |
| Al detectar un hallazgo que invalida resultados | Evaluación de impacto | Guía |
| Antes de la entrega | Documentación completa y sistema demostrable | Comisión |
| En la defensa | Demostración funcional en vivo, incluyendo las limitaciones | Comisión |

## 8. Recomendación para la demostración en la defensa

Orden sugerido, con la justificación de cada paso:

1. **Acceso y tablero.** Establece que el sistema funciona con dato real.
2. **Señalar las barras ámbar.** Introduce la frontera de información antes de que la pregunte
   la comisión.
3. **Alertas.** Muestra que el sistema interpreta, no solo calcula.
4. **Simulador.** Es la funcionalidad diferenciadora; advertir de antemano los segundos de
   espera y explicar por qué existen.
5. **Reporte de explicabilidad y tarjeta de aditividad.** Es el argumento de que la explicación
   es verificable, no ilustrativa.
6. **Conmutación de fuente de datos.** Cambiar una variable de entorno, reiniciar y mostrar la
   misma respuesta. Es la demostración de la arquitectura completa en treinta segundos.
7. **Consulta de reconstrucción del índice en SQL.** Cierra con auditabilidad: el cálculo se
   verifica sin ejecutar la aplicación.

El punto 6 es el que más difícil resulta de refutar: no es una afirmación sobre el diseño, es el
diseño ejecutándose.
