# Diseño de interfaz: maquetas y pantallas del sistema

Identificador del documento: **UI-SNED-01**

Contiene las maquetas de las cuatro pantallas, la justificación de cada decisión visual y el
procedimiento para capturar los pantallazos del sistema definitivo.

Las maquetas están derivadas de los componentes reales, no dibujadas aparte: cada región del
esquema corresponde a un elemento existente en `quanta/q4_cliente/src/`. Una maqueta que no
coincide con la pantalla implementada es peor que ninguna.

---

## 1. Principios de diseño de la interfaz

| Principio | Cómo se materializa |
|-----------|---------------------|
| La incertidumbre se muestra, no se esconde | El error medio acompaña siempre a la estimación, en la misma tarjeta |
| Lo acotado se distingue visualmente | Las barras de factores limitados por información no pública usan color ámbar; las plenas, azul |
| El sistema asiste, no decide | Cada pantalla cierra con un aviso que declara el alcance de lo mostrado |
| Nada se calcula en el cliente | La interfaz renderiza lo que el servicio entrega; no pondera ni deriva |
| Tema oscuro de alto contraste | Uso prolongado en sesiones de análisis |

Paleta efectivamente usada: fondo `#17222e`, borde `#24323f`, texto tenue `#9aacbd`, acento
azul `#4a9eda`, ámbar de advertencia `#d9a34f`, verde de referencia `#3fa87a`.

---

## 2. Pantalla 0 · Acceso

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                 Simulador Índice SNED                    │
│                                                          │
│         ┌──────────────────────────────────┐             │
│         │ Usuario                          │             │
│         ├──────────────────────────────────┤             │
│         │ Clave                            │             │
│         ├──────────────────────────────────┤             │
│         │           [ Entrar ]             │             │
│         └──────────────────────────────────┘             │
│                                                          │
│         (mensaje de error, si la credencial falla)       │
└──────────────────────────────────────────────────────────┘
```

Componente: `src/componentes/Login.tsx`. El mensaje de error no distingue entre usuario
inexistente y clave incorrecta.

---

## 3. Estructura común: barra y navegación

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Simulador Índice SNED          [ RBD 25520 ▾ ]  sostenedor   [ Salir ]  │
├──────────────────────────────────────────────────────────────────────────┤
│  [ 1. Dashboard ]  [ 2. Simulador ]  [ 3. Reporte XAI ]                   │
└──────────────────────────────────────────────────────────────────────────┘
```

El selector de establecimiento se alimenta exclusivamente de la lista de identificadores que
viaja en el token: un usuario no puede escribir un identificador ajeno porque la interfaz no
ofrece un campo de texto. La defensa real está en el servidor —control de jurisdicción—; esta es
la barrera de usabilidad que evita el intento.

Componente: `src/App.tsx`.

---

## 4. Pantalla 1 · Tablero

```
┌────────────────────────┬────────────────────────┬────────────────────────┐
│ ÍNDICE SNED ESTIMADO   │ MOTOR                  │ FACTORES ACOTADOS      │
│                        │                        │                        │
│        67.60           │  desagregado           │      5 de 6            │
│                        │                        │                        │
│ Escala 0-100 ·         │  versión 1.0.0         │ Limitados por          │
│ error medio ±2.31 pts  │                        │ información no pública │
└────────────────────────┴────────────────────────┴────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Aporte de cada factor al índice                                          │
│                                                                          │
│ Efectividad          ████████████████████████████  (azul)                │
│ Superación           ████████████████  (ámbar)                           │
│ Igualdad de Oport.   ███████████  (ámbar)                                │
│ Iniciativa           ███  (ámbar)                                        │
│ Integración          ██  (ámbar)                                         │
│ Mejoramiento         █  (ámbar)                                          │
│                                                                          │
│ ┌────────────┬───────┬────────┬────────┬──────────────────────────────┐  │
│ │ Factor     │ Peso  │ Valor  │ Aporte │ Restricción                  │  │
│ ├────────────┼───────┼────────┼────────┼──────────────────────────────┤  │
│ │ Efectividad│  37 % │  71.20 │  26.34 │ —                            │  │
│ │ Superación │  28 % │  58.40 │  16.35 │ Corrección por significancia │  │
│ │ …          │       │        │        │                              │  │
│ └────────────┴───────┴────────┴────────┴──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Alertas tempranas                                                        │
│  ▸ Trampa de superación            (borde rojo si la severidad es alta)  │
│    Detalle accionable de la alerta                                       │
│  ▸ Factor acotado dominante                                              │
│    Detalle                                                               │
└──────────────────────────────────────────────────────────────────────────┘

  Aviso de alcance del sistema
```

Componente: `src/paginas/Dashboard.tsx`. Gráfico de barras horizontales con color condicionado
por `es_acotado`.

**Decisión de diseño defendible:** la tabla acompaña al gráfico en lugar de sustituirlo. El
gráfico comunica proporción; la tabla entrega el número exacto y la restricción textual. Un
tablero que solo muestra la barra obliga a estimar a ojo un valor que tiene consecuencia
monetaria.

---

## 5. Pantalla 2 · Simulador

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Simulación de escenarios — curva ICE                                     │
│ Recorre el rango de una variable de gestión manteniendo fijas las        │
│ restantes. Es la base matemática del control, no una extrapolación.      │
│                                                                          │
│ [ SIMCE Matemática 4° básico ▾ ]                                         │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  Índice SNED                                                             │
│    ▲                                                                     │
│    │                                    ╭──────────                      │
│    │                          ╭─────────╯                                │
│    │                ╭─────────╯   ● ← posición actual (verde)            │
│    │      ╭─────────╯                                                    │
│    │──────╯                                                              │
│    └────────────────────────────────────────────▶                        │
│              SIMCE Matemática 4° básico                                  │
│                                                                          │
│ ┌────────────────────────────┬─────────────────────────────────────────┐ │
│ │ POSICIÓN ACTUAL            │ MONOTONICIDAD                           │ │
│ │        67.60               │        Verificada                       │ │
│ │ con SIMCE Mat. 4° = 271.3  │ Mover el control hacia arriba nunca     │ │
│ │                            │ baja el índice                          │ │
│ └────────────────────────────┴─────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘

  Advertencia de magnitud: hasta dónde es plausible el desplazamiento simulado
```

Componente: `src/paginas/Simulador.tsx`. Cinco palancas de gestión disponibles: medición
estandarizada de matemática y lectura de cuarto básico, tasa de aprobación, clima de convivencia
y dotación docente.

**Dos decisiones que sostienen la honestidad de la pantalla:**

1. **El punto verde marca la posición real.** Sin él, la curva invita a leer cualquier punto
   como alcanzable. Con él, queda claro cuánto hay que moverse.
2. **La monotonicidad se declara.** Si la curva no es monótona, la interfaz lo dice en vez de
   suavizarla. Una curva no monótona es información sobre el modelo, no un defecto de dibujo.

**Limitación conocida y visible:** la pantalla muestra "Simulando…" durante unos 4,6 segundos.
Son 54 inferencias por llamada. Está documentado y deliberadamente no resuelto.

---

## 6. Pantalla 3 · Reporte de explicabilidad

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Reporte de explicabilidad — valores de Shapley                           │
│ Cada barra es la contribución de una variable a la distancia entre la    │
│ predicción y el valor base.                                             │
│                                                                          │
│ [ Efectividad ▾ ]                                                        │
└──────────────────────────────────────────────────────────────────────────┘

┌───────────────────────┬───────────────────────┬──────────────────────────┐
│ VALOR BASE            │ ESTIMACIÓN DEL FACTOR │ ADITIVIDAD               │
│      64.12            │       71.20           │        OK                │
│                       │  +7.08 respecto del   │                          │
│                       │  promedio             │                          │
└───────────────────────┴───────────────────────┴──────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Contribuciones ordenadas por magnitud                                    │
│                                                                          │
│  SIMCE Matemática 4° básico      ────────────────▶  +4.21                │
│  SIMCE Lectura 4° básico         ──────────▶        +2.65                │
│  Tasa de aprobación              ────▶              +0.94                │
│  Sin medición de SIMCE 2° medio  ◀──                −0.72                │
└──────────────────────────────────────────────────────────────────────────┘
```

Componente: `src/paginas/ReporteXAI.tsx`.

**La tarjeta de aditividad es el elemento clave de esta pantalla.** Declara si la suma de las
contribuciones más el valor base reproduce la predicción dentro de la tolerancia. Es la
verificación de que la explicación explica *esta* predicción y no una aproximación cómoda. Una
explicación sin verificación de aditividad es una ilustración.

**Las ausencias se nombran.** Una variable sin medición aparece como "Sin medición de …" con su
contribución, no como un cero silencioso.

---

## 7. Estados no felices

Toda pantalla implementa tres estados, no solo el exitoso:

| Estado | Presentación |
|--------|--------------|
| Cargando | Panel con texto explícito de qué se está calculando |
| Error | Panel de error con el mensaje que devuelve el servicio, sin traducirlo ni suavizarlo |
| Sin jurisdicción | "Su perfil no tiene establecimientos asignados" |

Un establecimiento sin registros en la base analítica produce un error visible con esa frase
exacta. **Es el comportamiento correcto**: la regla de no inventar datos llega hasta la
interfaz.

---

## 8. Procedimiento para capturar los pantallazos del sistema definitivo

Las maquetas anteriores son el diseño. La tesis exige además capturas del sistema en
funcionamiento. Procedimiento reproducible:

1. Levantar la base, el servicio y la interfaz según `docs/manuales/MANUAL_INSTALACION.md`.
2. Entrar con un perfil que tenga jurisdicción sobre un establecimiento presente en el conjunto
   depurado.
3. Capturar en este orden, guardando en `docs/capturas/` con estos nombres:

| Archivo | Contenido | Qué debe verse |
|---------|-----------|----------------|
| `01_acceso.png` | Pantalla de acceso | Formulario limpio |
| `02_tablero.png` | Tablero completo | Las tres tarjetas, el gráfico con barras de ambos colores y la tabla |
| `03_alertas.png` | Panel de alertas | Al menos una alerta de severidad alta |
| `04_simulador.png` | Curva de sensibilidad | El punto verde de posición actual visible |
| `05_xai.png` | Reporte de explicabilidad | La tarjeta de aditividad en "OK" |
| `06_error_sin_datos.png` | Establecimiento sin registros | El mensaje de ausencia de registros |
| `07_documentacion_api.png` | `http://127.0.0.1:8000/docs` | La lista completa de rutas |

4. Capturar a ancho de ventana ≥ 1280 px: por debajo, el gráfico de barras comprime las
   etiquetas de factor.

La captura `06` merece estar en la tesis aunque muestre un error: es la evidencia visual de que
el sistema no rellena huecos para verse mejor.

---

## 9. Trazabilidad pantalla ↔ caso de uso

| Pantalla | Casos de uso | Rutas del servicio que consume |
|----------|-------------|-------------------------------|
| Acceso | CU-01 | `POST /auth/token` |
| Tablero | CU-02, CU-03 | `GET /prediccion/{rbd}`, `GET /prediccion/{rbd}/alertas` |
| Simulador | CU-04 | `POST /xai/simular` |
| Reporte XAI | CU-05 | `GET /xai/{rbd}/shapley` |
| Selector de la barra | CU-06 | lista de identificadores incluida en el token |
