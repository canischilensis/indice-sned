# Cuanto 4 — Cliente B2B

Interfaz de cuatro ventanas funcionales. Consume **exclusivamente** JSON tipado del cuanto 3
y, en la cuarta ventana, del cuanto 5. Desconoce por completo qué algoritmo opera detrás:
esa opacidad es el objetivo del Patrón Strategy, no una carencia.

| Ventana | Archivo | Qué responde | Servicio |
|---------|---------|--------------|----------|
| 1. Dashboard | `src/paginas/Dashboard.tsx` | Índice estimado, aporte por factor, alertas tempranas | Q3 `:8000` |
| 2. Simulador | `src/paginas/Simulador.tsx` | Curva ICE: qué ocurre si muevo esta variable | Q3 `:8000` |
| 3. Reporte XAI | `src/paginas/ReporteXAI.tsx` | Valores de Shapley: por qué obtuve este resultado | Q3 `:8000` |
| 4. Asesor | `src/paginas/Asesor.tsx` | Pregunta en lenguaje natural, con la traza de qué consultó | Q5 `:8010` |

La cuarta ventana apunta a **otro proceso**: el asesor es una unidad de despliegue aparte.
Si `:8010` está apagado, las tres primeras ventanas siguen operando y la cuarta lo informa
con esas palabras. Es la contrapartida visible de que el cuanto 5 se declara retirable.

El asesor **reenvía el token de la sesión** en cada consulta. El control de acceso lo evalúa
el cuanto 3 sobre la identidad del directivo, no sobre una cuenta de servicio compartida: sin
esa delegación, cualquier usuario alcanzaría por el agente establecimientos que la interfaz
le niega.

## Contrato de tipos

`src/tipos.ts` está escrito a mano y es la fuente de verdad durante el desarrollo.
Para regenerarlo desde el OpenAPI real del backend (con la API levantada en :8000):

```bash
npm run tipos     # escribe src/tipos-api.d.ts
```

Si los dos divergen, el generado manda: significa que el contrato del servicio cambió.

## Comandos

```bash
npm install
npm run dev       # http://localhost:5173
npm run lint      # tsc --noEmit
npm run build
```

Requiere el cuanto 3 corriendo en `http://127.0.0.1:8000` (`VITE_API_URL`). Para la cuarta
ventana, además el cuanto 5 en `http://127.0.0.1:8010` (`VITE_AGENTE_URL`):

```bash
uvicorn q5_agente.app:app --reload --app-dir quanta --port 8010
```

## Restricciones de producto que la interfaz debe respetar

1. **Nunca prometer retorno.** El índice normaliza contra los extremos nacionales: una mejora
   realista de 15-20 puntos SIMCE aporta del orden de 0,5 puntos. El simulador comunica
   dirección y sensibilidad. El texto ya viene en `advertencia_magnitud` desde la API.
2. **Mostrar los factores acotados.** El campo `es_acotado` marca los 5 factores limitados
   por información no pública (63 % de la ponderación). Se renderizan en ámbar, no se ocultan.
3. **Sin rankings brutos.** Perfiles institucionales contextualizados y focalizados en áreas
   de mejora, nunca tablas de posiciones descontextualizadas.
4. **La IA asiste, el directivo decide.** El aviso viaja en cada respuesta de predicción.
5. **La traza del asesor no es opcional.** Cada respuesta del agente muestra qué herramientas
   invocó y qué guardarrailes se aplicaron. Una respuesta sin herramientas exitosas no puede
   contener cifras: es lo que G-02 verifica antes de que el texto llegue a la pantalla.
