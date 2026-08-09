# Manual de usuario

Identificador del documento: **MU-SNED-01**
Destinatarios: equipo directivo, sostenedor y auditor.

Este manual explica qué hace el sistema, cómo usarlo y —lo más importante— **cómo interpretar lo
que muestra**. La última parte no es un adorno: el índice tiene consecuencia monetaria y una
lectura equivocada de una estimación puede orientar mal una decisión de gestión.

---

## 1. Qué hace y qué no hace este sistema

**Qué hace.** Estima el índice SNED de un establecimiento y sus seis factores a partir de datos
públicos, explica de dónde sale cada estimación, permite simular el efecto de mover una variable
de gestión y avisa de situaciones que merecen atención.

**Qué no hace:**

- No calcula el monto del beneficio. Eso es un acto administrativo del organismo.
- No predice el futuro. Estima el índice del ciclo a partir de las variables observadas.
- No decide. Entrega evidencia; la decisión estratégica sigue siendo del equipo directivo.
- No completa los datos que faltan. Si una fuente no cubre a un establecimiento, lo dice.

## 2. Entrar

Abra la dirección del sistema e introduzca usuario y clave. El sistema determina automáticamente
qué establecimientos puede ver: no hay que escribir identificadores.

Si su perfil no tiene establecimientos asignados, la pantalla lo indica. Contacte a quien
administra el sistema.

## 3. La barra superior

Contiene tres elementos:

- **Selector de establecimiento.** Solo lista los que su perfil tiene autorizados.
- **Su rol.** Determina qué puede ver.
- **Salir.** Cierra la sesión. También se cierra al cerrar la pestaña: la sesión no queda
  guardada en el navegador.

## 4. Ventana 1 · Tablero

### Las tres tarjetas superiores

| Tarjeta | Qué muestra | Cómo leerla |
|---------|-------------|-------------|
| **Índice SNED estimado** | El valor estimado en escala 0-100 y el error medio | El error medio es la desviación típica de la estimación. Un índice de 67,60 con error medio ±2,31 significa que el valor real está razonablemente cerca de ese rango, no que sea exactamente 67,60 |
| **Motor** | Qué modelo produjo la estimación y su versión | Sirve para trazar la estimación al artefacto que la generó |
| **Factores acotados** | Cuántos de los seis están limitados por información que el Estado no publica | Cuanto mayor sea este número, con más cautela debe tomarse la estimación |

### El gráfico de aporte por factor

Cada barra es lo que ese factor aporta al índice, ya multiplicado por su ponderación. La barra de
Efectividad es la más larga porque pesa 37 %, no necesariamente porque el establecimiento sea
excelente en ella.

**El color importa:**

- **Azul** — el factor se estima con información completa.
- **Ámbar** — el factor está acotado: falta información que el organismo no publica.

Cinco de los seis factores son ámbar. Eso representa el 63 % de la ponderación del índice.

### La tabla

Da los números exactos: peso, valor estimado, aporte y la restricción concreta de cada factor.
Léala junto al gráfico: el gráfico comunica proporción, la tabla comunica el valor.

### Las alertas

| Alerta | Qué está diciendo | Qué hacer |
|--------|-------------------|-----------|
| **Trampa de superación** | El establecimiento tiene efectividad alta y superación baja: ya está arriba y le queda poco margen de avance, que es justo lo que premia el segundo factor con más peso | Revisar si la estrategia depende de seguir subiendo resultados ya altos |
| **Riesgo normativo** | Los eventos de fiscalización acumulados superan el umbral | Revisar la gestión de convivencia y los procesos administrativos |
| **Caída IDPS** | El promedio de indicadores de desarrollo personal y social está bajo | Alimenta dos factores de menor peso pero es accionable en el corto plazo |
| **Factor acotado dominante** | La mayor parte de la estimación descansa en factores sobre los que el sistema tiene información incompleta | No es una alerta de gestión: es una advertencia sobre la confianza que merece el número |

La cuarta merece atención especial. No dice que el establecimiento esté mal: dice que **el sistema
sabe menos de lo que su número sugiere**.

## 5. Ventana 2 · Simulador

Responde a la pregunta: *si movemos esta variable, ¿qué pasa con el índice?*

### Cómo usarlo

1. Elija una variable de gestión entre las cinco disponibles.
2. Espere. **La simulación tarda unos cuatro a cinco segundos**: el sistema calcula el índice
   completo en cada punto de la curva, no interpola.
3. Lea la curva.

### Cómo leer la curva

- **El eje horizontal** es el valor de la variable que eligió.
- **El eje vertical** es el índice estimado.
- **El punto verde** es la posición actual del establecimiento. Es el elemento más importante del
  gráfico: sin él la curva invita a leer cualquier punto como alcanzable.
- **La pendiente** dice cuánto rinde moverse. Una pendiente plana significa que esa palanca no
  mueve el índice.

### La tarjeta de monotonicidad

Dice si mover la variable hacia arriba nunca baja el índice. Si aparece "No monótona", la relación
no es simple: hay tramos donde subir esa variable no ayuda. Es información sobre el modelo, y el
sistema la muestra en lugar de esconderla.

### Advertencia de magnitud

Al pie aparece hasta dónde es plausible el desplazamiento simulado. Un movimiento enorme en una
variable puede ser matemáticamente calculable y prácticamente inalcanzable.

## 6. Ventana 3 · Reporte de explicabilidad

Responde a: *¿por qué el sistema estimó este valor para este factor?*

### Las tres tarjetas

| Tarjeta | Significado |
|---------|-------------|
| **Valor base** | El valor promedio del factor en el conjunto de establecimientos. Es el punto de partida |
| **Estimación del factor** | El valor estimado para este establecimiento, con la diferencia respecto del promedio |
| **Aditividad** | Si dice **OK**, la explicación es matemáticamente exacta: las contribuciones suman la diferencia completa. Si dice "Revisar", la explicación es aproximada |

La tercera es la que hace confiable a esta pantalla. Una explicación que no verifica su aditividad
puede ser una ilustración plausible en lugar de una descomposición real.

### Las contribuciones

Cada barra es cuánto empuja una variable la estimación por encima o por debajo del promedio.
Positiva: empuja hacia arriba. Negativa: hacia abajo. Se ordenan por magnitud, así que **las
primeras son las que más explican**.

**"Sin medición de …"** significa que ese dato no existe para este establecimiento. El sistema lo
declara en lugar de tratarlo como un cero, porque no es lo mismo tener un resultado bajo que no
tener resultado.

## 7. Cómo interpretar bien lo que muestra el sistema

Cinco reglas de lectura. Son la parte de este manual que conviene no saltarse.

1. **La estimación no es el índice oficial.** Es una estimación con error conocido. Úsela para
   orientar, no para calcular derechos.
2. **Un factor ámbar merece menos confianza.** No porque el modelo sea malo, sino porque falta
   información pública.
3. **El aporte al índice no es el desempeño.** Un factor con aporte bajo puede ser un factor de
   poco peso, no un mal resultado.
4. **La simulación es una relación, no una promesa.** Muestra qué pasaría si esa variable cambiara
   manteniendo el resto fijo. En la realidad, mover una cosa mueve otras.
5. **Si el sistema dice que no hay datos, no los hay.** No se rellena para completar la pantalla.

## 8. Preguntas frecuentes

**¿Por qué el simulador tarda tanto?**
Cada punto de la curva es una estimación completa: el sistema calcula los seis factores en cada
uno. Es lento a propósito antes que aproximado.

**¿Por qué la primera consulta de la sesión demora más?**
Los modelos se cargan en el primer uso. Las consultas siguientes son rápidas.

**¿Por qué no aparece un establecimiento que sé que existe?**
Puede no estar en el conjunto depurado, o estar fuera de su jurisdicción. El sistema no revela la
existencia de establecimientos ajenos.

**¿Puedo consultar un establecimiento que no es mío?**
No. Aunque conozca el identificador, el sistema responde con una negativa de autorización.

**¿El sistema me dice si voy a recibir el beneficio?**
No. Estima el índice. El beneficio depende del ordenamiento dentro del grupo de comparación y de
decisiones administrativas del organismo.

**¿Qué hago si un número me parece equivocado?**
Consulte la ventana de explicabilidad: muestra exactamente qué variables sostienen la estimación.
Si la variable de entrada es incorrecta, el problema está en la fuente pública, no en el modelo.
