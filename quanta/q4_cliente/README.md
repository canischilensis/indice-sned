# Cuanto 4 — Cliente B2B

Interfaz de tres ventanas funcionales. Consume **exclusivamente** JSON tipado del cuanto 3.
Desconoce por completo qué algoritmo opera detrás: esa opacidad es el objetivo del
Patrón Strategy, no una carencia.

| Ventana | Archivo | Qué responde |
|---------|---------|--------------|
| 1. Dashboard | `src/paginas/Dashboard.tsx` | Índice estimado, aporte por factor, alertas tempranas |
| 2. Simulador | `src/paginas/Simulador.tsx` | Curva ICE: qué ocurre si muevo esta variable |
| 3. Reporte XAI | `src/paginas/ReporteXAI.tsx` | Valores de Shapley: por qué obtuve este resultado |

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

Requiere el cuanto 3 corriendo en `http://127.0.0.1:8000`. Configurable vía `VITE_API_URL`.

## Restricciones de producto que la interfaz debe respetar

1. **Nunca prometer retorno.** El índice normaliza contra los extremos nacionales: una mejora
   realista de 15-20 puntos SIMCE aporta del orden de 0,5 puntos. El simulador comunica
   dirección y sensibilidad. El texto ya viene en `advertencia_magnitud` desde la API.
2. **Mostrar los factores acotados.** El campo `es_acotado` marca los 5 factores limitados
   por información no pública (63 % de la ponderación). Se renderizan en ámbar, no se ocultan.
3. **Sin rankings brutos.** Perfiles institucionales contextualizados y focalizados en áreas
   de mejora, nunca tablas de posiciones descontextualizadas.
4. **La IA asiste, el directivo decide.** El aviso viaja en cada respuesta de predicción.
