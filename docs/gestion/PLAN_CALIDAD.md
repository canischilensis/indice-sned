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
| `access violation` en un hilo secundario durante la suite en Windows, con marcos de pila corruptos. Código de salida cero y todas las pruebas pasan | Media | Abierto, sin diagnóstico. Se descartó la hipótesis del cliente `httpx`: cerrarlo no lo eliminó, solo lo movió de lugar. El 2026-08-10 se ejecutó `pytest -q -p no:faulthandler` y no apareció, **pero tampoco apareció en cinco corridas de control sin la bandera ese mismo día**: el experimento no distingue nada y se declara no concluyente. El fallo no se reprodujo en toda la sesión |
| La latencia que espera un usuario no está medida | Media | Abierto. CP-17 acota el bucle contra un doble de respuesta fija. El 2026-08-10 se midió 31 ms contra el doble, 5.906 ms en la primera consulta al servicio real y 0 ms en la segunda: la diferencia es la carga en frío de los artefactos, no el cómputo. Faltan dos series distintas, arranque y régimen |

**Defectos cerrados.** Se conservan en el registro. Un defecto que se corrige y
se borra deja de enseñar, y el valor de este plan está en lo que el proyecto
aprendió equivocándose, no en la apariencia de no haberse equivocado.

| Defecto | Severidad | Cierre |
|---------|-----------|--------|
| Tercera copia de los códigos de factor en el adaptador determinista: pedía `SUPERACR` y el servicio la rechazaba | Alta | 2026-08-10. La copia se retiró; el código se resuelve contra el `enum` del esquema de la herramienta |
| La explicación por factor devolvía el código y no el nombre: un directivo leía `SUPERAR` | Media | 2026-08-10. `RespuestaExplicacion` declara `nombre`, resuelto contra el catálogo oficial |
| CP-11 aprobaba por el mensaje de error: la frase exigida aparecía dentro del código mal escrito | Alta | 2026-08-10. Se corrigió el ruteo y el caso pasó a rojo honesto antes de volver a verde |
| La redacción omitía la ausencia de dato por ser la quinta contribución en magnitud | Alta | 2026-08-10. Toda variable con `valor: null` se nombra siempre, entre o no entre las tres mayores |
| El veredicto de la suite dependía del entorno de la shell: `pytest` pasaba en una terminal y fallaba en otra | Alta | 2026-08-10. `tests/unitarias/q5/conftest.py` aísla las variables del cuanto 5, derivadas de los campos de la configuración |
| El proveedor externo respondía en Markdown, que la ventana pinta literal, y con punto decimal en lugar de coma | Media | 2026-08-10. Corregido en dos capas: se pide en el mensaje de sistema y se normaliza en el bucle, porque una instrucción a un modelo es una petición y no una garantía |
| Una consulta sin factor reconocible se respondía sobre Efectividad sin avisar | Alta | 2026-08-10. Sin factor inferible se rutea al diagnóstico general, que nombra los seis. Un error silencioso es peor que uno visible: el anterior producía una respuesta correcta sobre la pregunta equivocada |
| La interfaz mostraba al rol de auditoría un mensaje que decía lo contrario de su alcance real | Media | 2026-08-10. Cerrado por decisión registrada en ADR-007: el rol se sirve por API. La pantalla distingue ahora el caso y el manual lo declara. Construir la búsqueda por identificador queda como trabajo futuro |
| El cliente nunca leyó su configuración: Vite buscaba un `.env` que nunca existió y las direcciones venían de constantes de reserva en `api.ts` | Alta | 2026-08-10. `envDir` apunta a la raíz: un solo archivo de configuración. Se agrega `tests/arquitectura/test_variables_del_cliente.py`, porque exponer la raíz al empaquetador depende de que ninguna credencial lleve prefijo `VITE_` |
| Los orígenes CORS del asesor estaban escritos a mano en el código | Media | 2026-08-10. `AGENTE_CORS_ORIGENES` pasa a configuración. Una dirección de red no es una constante del programa |
| El estado del repositorio dependía de la instalación de git de quien preguntara: sobre el mismo commit, un Windows informaba el árbol limpio y un Linux setenta archivos modificados | Media | 2026-08-10. No existía `.gitattributes`: el fin de línea lo decidía el `core.autocrlf` de cada máquina. Se declara la normalización en el repositorio, con los binarios explícitos y los guiones de shell forzados a LF |
| `AGENTE_MODELO` era una sola variable compartida por cuatro proveedores: al cambiar de proveedor, el modelo del anterior se filtraba y producía una evaluación entera falsa | Alta | 2026-08-10. El modelo local pasa a tener campo propio, la fábrica falla ruidosamente ante un modelo de otro proveedor, y el arnés declara qué hace con él al mover la variable |
| El mensaje de sistema usaba la misma raíz léxica que G-03 prohíbe: el modelo parafraseaba la instrucción y su respuesta correcta se retenía | Alta | 2026-08-15. Detectado en uso real, sobre una de las preguntas sugeridas por la propia interfaz. G-03 pasa a evaluar oración por oración respetando la negación, la instrucción deja de contener la raíz, y una prueba nueva exige que el mensaje de sistema cumpla la política que impone |
| Una corrida de veintiséis minutos no imprimía nada y era indistinguible de un proceso colgado: quien la lanzó la interrumpió dos veces | Media | 2026-08-10. El arnés informa cada caso al terminarlo y admite correr los primeros N, marcando la salida como parcial |

### 9.1 Reglas que salen de defectos reales

No son principios importados de un manual: cada una nació de un fallo de este
proyecto y se escribió el día que costó tiempo.

| Regla | Defecto que la origina |
|-------|------------------------|
| Una duplicación aceptada por ADR exige una prueba **por copia**, no una por el par | Los códigos de factor vivían en tres lugares y la prueba comparaba dos. La tercera se desincronizó y la suite siguió en verde |
| Un doble de prueba refleja el **sistema**, nunca la implementación | El doble replicaba la constante equivocada y bendecía el error que debía detectar |
| El veredicto de la suite no puede depender del entorno de quien la ejecuta | La precedencia «variable del proceso sobre archivo» es correcta en operación y contaminante en pruebas: mismo commit, dos resultados |
| Tampoco el estado del repositorio | Sin `.gitattributes`, el mismo commit se veía limpio en Windows y con setenta archivos modificados en Linux. Toda condición que decida un veredicto se fija en el repositorio, no en la máquina |
| Una herramienta nueva no entra al catálogo por omisión | Agregar una herramienta cambia el ruteo. La de doctrina se enciende por configuración, para que los veinte casos y la comparación entre orquestadores no queden medidos contra otro catálogo sin que nadie lo decidiera |
| La evidencia tiene grados y la auditoría debe distinguirlos | Una cifra leída de un documento no es una medición. G-02 pasó de dos veredictos a tres, y el motivo del rechazo dice cuál de los dos problemas ocurrió, porque se corrigen distinto |
| Una prueba que aprueba por un camino de error no verifica: coincide | CP-11 exigía la cadena `superac` y la obtenía del mensaje «Factor desconocido: SUPERACR» |
| Primero el comportamiento, después el criterio | Ante una prueba que no medía su intención declarada, se corrigió el agente y recién entonces se endureció el caso. Al revés sería ajustar la prueba a lo que el sistema hace |
| Lo que se le pide a un modelo se verifica aparte | Se le pidió responder en prosa plana y con coma decimal. La garantía la da una normalización en el bucle, no la instrucción. Vale para el formato igual que G-02 vale para las cifras |
| Un error silencioso es peor que uno visible | El ruteo adivinaba un factor y respondía bien sobre la pregunta equivocada. El defecto anterior —un código mal escrito— producía un fallo que se veía y por eso se corrigió; este no dejaba rastro |
| Una capacidad sin interfaz se declara, no se disimula | El rol de auditoría existe y está verificado en el servicio. Se decidió no construirle ventana y dejarlo escrito en un ADR, en lugar de recortar el rol para que calzara con la pantalla |
| Verificar contra una línea base no sustituye verificar contra el sistema real | Los veinte casos corren contra el adaptador determinista, que cumple el contrato de formato por construcción. El defecto solo apareció en la primera consulta a un proveedor externo |
| **Un resultado sin consumo no es un resultado** | Una evaluación de veinte casos devolvió 0/20 con cero tokens y cero llamadas al modelo: parecía decir que un modelo local ruteaba pésimo y en realidad nunca se le preguntó nada. Antes de leer una tabla se comprueba que hubo consumo |
| **La métrica válida depende de la variable que se mueve** | «Casos aprobados» sirve cuando ambos lados redactan igual —eje de orquestadores— y castiga la variación léxica cuando uno de los lados es generativo —eje de proveedores—. Ahí la métrica es ruteo más guardarraíles. Se declara antes de mirar el resultado, no después |
| **Una regla no puede prohibir lo que la instrucción enseña** | El mensaje de sistema le pedía al modelo advertir que «ninguna mejora lo garantiza», y G-03 retenía toda respuesta con esa raíz. Prompt y guardarrail se verifican uno contra otro, no por separado |
| **Una prueba que esquiva la palabra que falla no prueba nada** | El caso de lectura prudente de G-03 estaba escrito con «asegura», justo el sinónimo que no fallaba. Pasó verde durante todo el desarrollo mientras el defecto seguía ahí |
| **La expectativa se escribe antes de medir** | El módulo del proveedor local declaró que esperaba doce aciertos de veinte. Midió diecisiete. Sin la predicción escrita, cualquier cifra habría confirmado lo que se pensara después |

## 10. Lo que este plan no cubre

| Elemento | Motivo |
|----------|--------|
| Pruebas de carga y concurrencia | El sistema atiende a equipos directivos, no a tráfico masivo; el requisito de concurrencia no está establecido |
| Pruebas de penetración | Fuera del alcance del proyecto de título |
| Auditoría de accesibilidad | Reconocido como brecha; no hay requisito formal establecido |

## 11. Historial de modificaciones

Nada se elimina de este documento. Lo que deja de ser cierto se marca como
superado y conserva su texto: la trazabilidad de una decisión incluye lo que se
creía antes de tomarla.

| Fecha | Sección | Cambio | Motivo |
|-------|---------|--------|--------|
| 2026-08-10 | 9 | Se agrega la tabla de defectos cerrados con cinco entradas | Cinco defectos encontrados por el uso durante la verificación de la cuarta ventana |
| 2026-08-10 | 9.1 | Sección nueva: cinco reglas derivadas de defectos reales | Las reglas existían en la cabeza del autor y en comentarios de código; faltaba registrarlas donde el plan las pueda exigir |
| 2026-08-10 | 11 | Sección nueva: este historial | Se adopta la convención de conservar el registro de modificaciones en todos los documentos |
| 2026-08-10 | 9 | Se registran dos defectos abiertos que no estaban en ningún documento: el `access violation` de Windows y la latencia percibida sin medir | Vivían en notas de trabajo. Un defecto conocido que no está en el plan no está declarado: está olvidado a medias |
| 2026-08-10 | 9 | Se cierra el defecto de formato del proveedor externo y se corrige la atribución de la latencia: fue arranque en frío, no cómputo | Una medición aislada se había declarado como propiedad del sistema |
| 2026-08-10 | 9.1 | Dos reglas nuevas: lo que se le pide a un modelo se verifica aparte, y la línea base no sustituye al sistema real | Ambas salen del mismo defecto: la evaluación completa corría contra un proveedor que cumple el contrato por construcción |
| 2026-08-15 | 9 y 9.1 | Se cierra el defecto de G-03 contra el mensaje de sistema y se agregan dos reglas sobre como se verifican las instrucciones y las pruebas | Lo encontro el uso real, no la suite: 256 pruebas verdes con el defecto adentro |
| 2026-08-10 | 9 y 9.1 | Se cierran dos defectos de la evaluación —modelo compartido entre proveedores y corrida sin señal de avance— y se agregan tres reglas sobre cómo leer una medición | Los tres salen de la misma sesión: una tabla falsa que parecía un hallazgo, y una corrida interrumpida por falta de información |
| 2026-08-10 | 9 y 9.1 | Se cierran dos defectos más —el factor adivinado en silencio y el mensaje al rol de auditoría— y se agregan sus dos reglas | El primero salió a la luz al retirar la copia de códigos; el segundo al preparar la captura del perfil sin establecimientos |
