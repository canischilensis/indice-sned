# Manual de monitorización

Identificador del documento: **MM-SNED-01**

Define qué observar para saber si el sistema está sano, con qué frecuencia y qué hacer cuando algo
se sale de rango.

La monitorización de este sistema tiene una particularidad frente a una aplicación transaccional
común: **puede estar operando perfectamente y entregando estimaciones cada vez peores**. Un
servicio que responde 200 en todas sus rutas no dice nada sobre si el modelo sigue siendo válido.
Por eso la monitorización se organiza en tres capas.

---

## 1. Las tres capas

| Capa | Pregunta que responde | Frecuencia |
|------|----------------------|-----------|
| **Disponibilidad** | ¿Responde? | Continua |
| **Integridad del dato** | ¿Lo que responde está completo y es correcto? | Tras cada carga y semanalmente |
| **Validez del modelo** | ¿Sigue siendo cierto lo que estima? | Bianual, por ciclo del índice |

La tercera es la que se olvida y la que más importa en un sistema predictivo.

---

## 2. Capa 1 · Disponibilidad

### Comprobación básica

```
GET /api/v1/salud
```

Debe responder 200. Es la comprobación mínima para un supervisor externo.

### Indicadores

| Indicador | Valor esperado | Umbral de alarma |
|-----------|---------------|------------------|
| Disponibilidad del servicio | 200 en la ruta de salud | Cualquier otro código |
| Conexiones activas a la base | Estable | Crecimiento sostenido: fuga de sesiones |
| Memoria del proceso de aplicación | Estable tras la primera carga de artefactos | Crecimiento sostenido: fuga |
| Latencia de predicción | < 300 ms | > 1 s de forma sostenida |
| Latencia de simulación | ≈ 4,6 s | > 8 s |

**Sobre la memoria:** es normal que el proceso crezca de golpe la primera vez que alguien pide una
predicción o una explicación. Es la carga diferida de los artefactos, que pesan 210 MB. Lo anómalo
es que siga creciendo después.

---

## 3. Capa 2 · Integridad del dato

### Cobertura de variables

```
GET /api/v1/salud/composicion
```

| Métrica | Valor esperado | Qué significa una desviación |
|---------|---------------|------------------------------|
| Cobertura | ≈ 0,814 (35 de 43) | Si baja, el repositorio dejó de entregar variables que el modelo requiere |
| **Cobertura = 0,0** | — | El servicio no está leyendo la fuente de datos. Revisar la variable de adaptador y la cadena de conexión |

Este indicador es el más informativo del sistema: una cobertura de cero significa que la
aplicación arrancó bien, responde bien y **estima sobre nada**.

### Verificación del cálculo del índice

Tras cada carga, y periódicamente:

```sql
SELECT max(abs(v.indicer_calculado - r.indicer)) AS discrepancia_maxima,
       count(*)                                  AS filas_comparadas
FROM   hechos.v_indicer_reconstruido v
JOIN   hechos.sned_resultado r USING (rbd, periodo_id)
WHERE  v.n_factores = 6;
```

| Métrica | Valor esperado | Acción si se desvía |
|---------|---------------|--------------------|
| Discrepancia máxima | ≤ 0,001 | Investigar precisión de columnas y proceso de carga. **No ajustar el umbral** |
| Filas comparadas | ≈ 44.679 | Una caída indica pérdida de filas en la carga |

### Suma de ponderaciones

```sql
SELECT sum(ponderacion) FROM core.factor_sned;
```

Debe ser exactamente 1,0. La base lo impone con un disparador diferido, así que un valor distinto
solo puede aparecer si alguien desactivó el disparador.

### Integridad referencial y cuarentena

| Comprobación | Consulta o archivo | Esperado |
|-------------|-------------------|----------|
| Hechos huérfanos | Recuento contra `core.establecimiento` | 0 |
| Registros en cuarentena por fuente | `data/interim/cuarentena/*.parquet` | Estable entre cargas equivalentes |
| Cobertura de llave por fuente | Reporte de calidad de ingesta | ≥ 0,95 |

Un aumento brusco de la cuarentena entre dos cargas del mismo periodo indica que la fuente pública
cambió de formato.

### Registro de modelos

```
GET /api/v1/salud/registro
```

Verifica que los nueve artefactos estén presentes y con tamaño esperado. Un artefacto ausente
provoca fallo en el primer uso, no al arrancar: la carga diferida retrasa el síntoma.

---

## 4. Capa 3 · Validez del modelo

Se ejecuta una vez por ciclo bianual del índice, cuando hay datos nuevos. No es continua porque el
fenómeno no lo es.

### Verificación de deriva

Contrasta la distribución de las variables actuales contra la línea base registrada durante el
entrenamiento (CTRL-03).

| Resultado | Interpretación | Acción |
|-----------|---------------|--------|
| Sin desplazamiento significativo | El modelo sigue operando sobre la población que aprendió | Continuar |
| Desplazamiento en variables de bajo peso | Vigilar | Registrar y volver a evaluar en el ciclo siguiente |
| Desplazamiento en variables de Efectividad | El factor de mayor peso opera fuera de su dominio | **Reentrenar** |

El caso relevante para este dominio es la discontinuidad postpandemia: un desplazamiento de esa
magnitud invalida un modelo entrenado antes, aunque el sistema siga respondiendo con normalidad.

### Comparación de métricas

Al reentrenar, el modelo candidato solo se aprueba si supera al vigente **y** la superioridad se
sostiene con intervalos de confianza y prueba t pareada. Un R² mayor por sí solo no basta.

---

## 5. Monitorización de seguridad

| Evento | Dónde observarlo | Qué significa |
|--------|-----------------|---------------|
| Respuestas 403 | Bitácora del servicio | Intentos de acceso fuera de jurisdicción. Aisladas son normales; repetidas desde un mismo perfil, no |
| Respuestas 401 | Bitácora del servicio | Credenciales inválidas o token expirado |
| Accesos servidos | `app.auditoria` | Tabla creada; el registro efectivo está pendiente junto con la migración del directorio de usuarios |

---

## 6. Calendario

| Frecuencia | Comprobación |
|-----------|--------------|
| Continua | Ruta de salud |
| Diaria | Memoria y conexiones; respaldo de la base completado |
| Semanal | Cobertura de composición; latencias |
| Tras cada carga | Verificación del cálculo del índice; conteos por tabla; suma de ponderaciones |
| Tras cada despliegue | Suite de pruebas; comprobación de composición |
| Bianual | Deriva de distribuciones; evaluación de reentrenamiento |

---

## 7. Guía de diagnóstico

| Síntoma | Causa probable | Comprobación | Solución |
|---------|---------------|--------------|----------|
| Cobertura 0,0 | El servicio no lee la fuente | Variable de adaptador y cadena de conexión | Corregir la configuración y reiniciar |
| Todas las predicciones fallan con 500 | Artefacto ausente o incompatible | Ruta de registro | Reponer el artefacto o fijar la versión de la librería |
| Un establecimiento responde 404 | No está en el conjunto depurado | Consultar `core.conjunto_entrenamiento` | Ninguna: es el comportamiento correcto |
| Un usuario recibe 403 en su propio establecimiento | Jurisdicción mal declarada | Directorio de autorización | Corregir la lista de identificadores del perfil |
| La discrepancia del índice supera 0,001 | Pérdida de precisión en la carga | Precisión de las columnas numéricas | Corregir el esquema y recargar. **No relajar el umbral** |
| La simulación supera los 8 s | Recursos del servidor de aplicación | Uso de CPU | Revisar recursos; la latencia base de 4,6 s es conocida |
| El ordenamiento intragrupo es lento | Recálculo de funciones de ventana | Plan de ejecución de la vista | Limitación conocida; la solución de fondo es materializar la vista |

---

## 8. Qué no está instrumentado

Se declara para que la ausencia sea una decisión y no un descuido.

| Elemento | Estado | Motivo |
|----------|--------|--------|
| Métricas centralizadas y tableros de observabilidad | No implementado | Un servicio, una base; el costo de la infraestructura supera el beneficio en esta escala |
| Alertas automáticas por correo o mensajería | No implementado | Sin operación continua establecida |
| Registro de inferencias en base de datos | Tablas creadas, escritura pendiente | Depende de la migración del directorio de usuarios |
| Trazas distribuidas | No aplica | No hay servicios encadenados |
