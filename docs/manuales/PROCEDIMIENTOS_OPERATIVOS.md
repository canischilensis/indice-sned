# Procedimientos operativos

Identificador del documento: **PR-SNED-01**

Procedimientos que complementan las funcionalidades del sistema pero que no ocurren dentro de la
aplicación. Cada uno indica quién lo ejecuta, cuándo, en qué orden y **cómo verificar que salió
bien**.

Un procedimiento sin verificación es una lista de deseos.

---

## Índice de procedimientos

| Código | Procedimiento | Frecuencia | Responsable |
|--------|--------------|-----------|-------------|
| PR-01 | Incorporación de un nuevo ciclo del índice | Bianual | Ingeniero de datos |
| PR-02 | Reentrenamiento y publicación de modelos | Bianual o ante deriva | Ingeniero de datos |
| PR-03 | Incorporación de una fuente de datos nueva | Ante disponibilidad | Ingeniero de datos |
| PR-04 | Actualización de las ponderaciones oficiales | Ante cambio normativo | Ingeniero de datos |
| PR-05 | Alta y baja de usuarios | Bajo demanda | Administrador |
| PR-06 | Respaldo y restauración | Diaria / ante incidente | Administrador |
| PR-07 | Despliegue de una versión nueva | Por entrega | Desarrollador |
| PR-08 | Conmutación de la fuente de datos | Ante incidente o demostración | Administrador |
| PR-09 | Atención de una discrepancia reportada por un usuario | Bajo demanda | Desarrollador |

---

## PR-01 · Incorporación de un nuevo ciclo del índice

**Cuándo:** cuando el organismo publica los resultados de un ciclo nuevo.

1. Descargar las fuentes del ciclo según `docs/FUENTES.md` y depositarlas en `data/raw/`.
2. Ejecutar la ingesta de cada fuente. Revisar el reporte de calidad: **si la cobertura de llave
   cae bajo 0,95, detenerse e investigar antes de continuar**.
3. Comparar el volumen de la cuarentena con el del ciclo anterior. Un aumento brusco indica cambio
   de formato en la fuente, no deterioro del dato.
4. Insertar el periodo nuevo en `core.periodo`.
5. Ejecutar la carga. Es idempotente: no duplica lo ya cargado.
6. Refrescar la vista materializada de entrenamiento.
7. Ejecutar la verificación del cálculo del índice.
8. Ejecutar la verificación de deriva (PR-02, paso 1).

**Verificación de cierre:** discrepancia máxima ≤ 0,001 y conteos por tabla coherentes con el
ciclo anterior más el nuevo.

**Riesgo:** el paso 4 se olvida con facilidad. Sin el periodo insertado, la carga rechaza las
filas por integridad referencial y el síntoma parece un problema de datos.

---

## PR-02 · Reentrenamiento y publicación de modelos

**Cuándo:** por ciclo bianual, o cuando la verificación de deriva señale desplazamiento en
variables de peso alto.

1. **Verificar deriva** contra la línea base registrada. Si no hay desplazamiento significativo,
   detenerse: reentrenar sin motivo introduce variación sin ganancia.
2. Reconstruir la matriz de entrenamiento desde la vista materializada.
3. **Ejecutar la auditoría anti-fuga.** Confirmar que ni los seis factores, ni el índice oficial,
   ni la agrupación de comparación aparecen entre las variables de entrada. El R² del predictor
   trivial debe ser aproximadamente cero.
4. Entrenar con particionamiento agrupado, para que un mismo establecimiento no aparezca en
   entrenamiento y prueba.
5. Comparar el candidato contra el vigente: **no basta un R² mayor**; la superioridad debe
   sostenerse con intervalos de confianza y prueba t pareada.
6. Si supera, depositar los artefactos en el registro y actualizar sus metadatos, **incluyendo la
   versión de la librería de aprendizaje**.
7. Registrar la nueva línea base de distribuciones.
8. Reiniciar el servicio y verificar la ruta de composición y una explicación completa.

**Verificación de cierre:** la aditividad de la explicación se verifica y la cobertura se mantiene.

**Regla:** si el candidato no supera al vigente, **se conserva el vigente**. Un modelo nuevo por
ser nuevo no es una mejora.

---

## PR-03 · Incorporación de una fuente de datos nueva

**Cuándo:** cuando aparece una fuente pública relevante.

1. Caracterizar la fuente: formato, codificación, llave, ventana temporal, cobertura.
2. Registrarla en el catálogo de fuentes.
3. Elegir el ingestor por formato. Si ninguno sirve, crear uno nuevo heredando de la plantilla:
   **solo se redefine la lectura**, nunca el orden de los pasos.
4. Declarar las reglas de admisión componiendo las existentes.
5. Insertar el tipo de indicador en `core.tipo_indicador`. **Añadir una fuente inserta filas, no
   altera el esquema.**
6. Ejecutar la ingesta y revisar el reporte de calidad.
7. Cargar y verificar los conteos.
8. Documentar el origen y el procedimiento de redescarga en `docs/FUENTES.md`.

**Verificación de cierre:** la fuente produce parquet y cuarentena, y las filas llegan a
`hechos.indicador_anual`.

**Restricción:** si la fuente contiene información derivada del índice o de sus factores, **no se
incorpora como variable de entrada**. Sería fuga.

---

## PR-04 · Actualización de las ponderaciones oficiales

**Cuándo:** cuando cambia el decreto que fija los pesos.

Es un **cambio crítico**: altera todo índice reconstruido. Requiere evaluación de impacto según el
plan de gestión de cambios.

1. Obtener el texto normativo y anotar la fuente.
2. Actualizar `core.factor_sned` **dentro de una sola transacción**. El disparador es diferido
   precisamente para esto: durante la actualización los pesos no suman uno, y una restricción
   inmediata haría imposible el cambio.
3. Actualizar `contratos/catalogo_factores.json` para que coincida con la tabla.
4. Ejecutar la inicialización, que valida la correspondencia entre ambos.
5. Reejecutar la verificación del cálculo del índice.
6. Registrar el cambio como decisión de arquitectura.

**Verificación de cierre:** la suma de ponderaciones es exactamente 1,0 y la inicialización no
aborta.

**Regla no negociable:** si el archivo y la tabla divergen, **se corrige el archivo**. El DDL es la
fuente de verdad.

---

## PR-05 · Alta y baja de usuarios

**Estado actual:** el directorio de autorización vive en memoria, en
`quanta/q3_servicio/core/seguridad.py`. No hay administración por interfaz.

**Procedimiento provisional:**

1. Editar el directorio añadiendo o quitando el perfil, con su rol y su lista de identificadores.
2. **Verificar que cada identificador exista en el conjunto depurado.** Un identificador que no
   sobrevivió a la depuración produce un error de "sin registros en la base analítica" al entrar.
3. Reiniciar el servicio.
4. Verificar entrando con el perfil.

**Procedimiento previsto** una vez migrado a `app.usuario`: alta en la tabla, asignación de
jurisdicción en `app.usuario_establecimiento`, sin reinicio.

---

## PR-06 · Respaldo y restauración

### Respaldo

| Elemento | Método | Frecuencia | Retención |
|----------|--------|-----------|-----------|
| Base de datos | Volcado lógico completo | Diaria | 30 días |
| Artefactos de modelo | Copia versionada fuera del repositorio | Por publicación | Todas las versiones |
| Esquema | Versionado en el repositorio | Por cambio | Historial completo |
| Datos crudos | Redescargables desde la fuente | — | — |

### Restauración

1. Restaurar el volcado sobre una base vacía.
2. Volver a crear las vistas.
3. Refrescar la vista materializada.
4. Ejecutar la verificación del cálculo del índice.
5. Reponer el directorio de artefactos.
6. Levantar el servicio y verificar la ruta de composición.

**Verificación de cierre:** discrepancia máxima ≤ 0,001 y cobertura ≈ 0,814.

**Alternativa completa sin volcado:** el esquema se reconstruye desde el repositorio y la carga es
idempotente, de modo que el sistema puede rehacerse desde cero con los archivos columnares.

---

## PR-07 · Despliegue de una versión nueva

1. Confirmar que la suite pasa en integración continua.
2. Si hay cambios de esquema, ejecutarlos **antes** de desplegar el código.
3. Desplegar el servidor de aplicación.
4. Compilar y publicar la interfaz.
5. Verificar en orden: ruta de salud, composición, una predicción, una explicación, una simulación.
6. Si algo falla, revertir el código; el esquema se revierte solo si el cambio era incompatible.

**Verificación de cierre:** los cinco puntos del paso 5 responden correctamente.

**Nota:** el primer uso de predicción o explicación tras el despliegue es lento por la carga
diferida de artefactos. No confundirlo con una degradación.

---

## PR-08 · Conmutación de la fuente de datos

**Cuándo:** ante indisponibilidad de la base, o para demostrar el sistema sin infraestructura.

1. Fijar la variable de adaptador al valor `parquet`.
2. Reiniciar el servicio.
3. Verificar la ruta de composición.
4. Para volver: fijarla en `postgres` y reiniciar.

**Verificación de cierre:** la ruta de composición informa el adaptador activo y una cobertura
distinta de cero.

**Limitación:** el modo columnar es de solo lectura y no expone el ordenamiento intragrupo con la
misma mecánica de desempate. Es un modo de contingencia, no un equivalente pleno.

---

## PR-09 · Atención de una discrepancia reportada por un usuario

**Cuándo:** un usuario informa que un valor le parece equivocado.

1. Reproducir la consulta con el mismo identificador y periodo.
2. Abrir la ventana de explicabilidad: muestra qué variables sostienen la estimación.
3. Contrastar esas variables contra el dato persistido.
4. Contrastar el dato persistido contra el archivo de origen.
5. Clasificar el origen de la discrepancia:

| Origen | Acción |
|--------|--------|
| El dato de la fuente pública es incorrecto | Documentar en `docs/FUENTES.md`. **No corregir el dato**: el sistema refleja la fuente |
| La carga perdió precisión | Corregir el esquema y recargar (cambio crítico) |
| El modelo estima mal en ese caso | Registrar como caso de interés para el próximo reentrenamiento |
| El usuario esperaba el índice oficial | Es una diferencia de expectativa: el sistema estima, no calcula el oficial |

**Verificación de cierre:** la discrepancia queda clasificada en una de las cuatro categorías, con
su evidencia.

**Regla:** ningún dato se ajusta a mano en la base. Si el valor es incorrecto, o se corrige el
proceso de carga o se documenta el defecto de la fuente.
