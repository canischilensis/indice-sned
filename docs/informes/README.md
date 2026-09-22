# Informes de avance

Documentos de hito entregados a la carrera. Se versionan aquí por dos razones: para que el
repositorio contenga lo que se afirmó de él, y para que las figuras que el informe cita
puedan comprobarse contra `docs/diagramas/`.

| Hito | Archivo | Fecha de entrega | Estado |
|---|---|---|---|
| 2 | `Informe_Hito2.docx` · `Informe_Hito2.pdf` | 9 de agosto de 2026 | Entregado |
| 2 | `INFORME_HITO_2.md` | — | Fuente en Markdown del anterior |

## Sobre la version en Markdown

`INFORME_HITO_2.md` es la fuente de la que se genero el documento Word, no una copia
posterior. Difiere de lo entregado en dos puntos, y conviene saber cuales:

1. **Las rutas de las figuras son relativas a esta carpeta** (`../diagramas/...`), para que
   el documento se vea con sus figuras al abrirlo en GitHub. El .docx lleva las imagenes
   incrustadas y no depende de rutas.
2. **La Figura 4 del .docx esta partida en dos** (`02a` y `02b`). En el Markdown sigue siendo
   `02_patrones` completa. El motivo esta explicado en `docs/diagramas/README.md`.

## Lo que el informe declara como faltante

El informe declara, en vez de omitir, lo que no existia al momento de entregarlo. Sigue sin
existir y esta pendiente:

- **`docs/capturas/` no existe.** Faltan las capturas del sistema en funcionamiento. Con la
  cuarta ventana incorporada al cliente, son ocho: tablero, simulador, reporte de
  explicabilidad, asesor de gestion con su traza, la pantalla de acceso, la vista de un
  perfil sin establecimientos asignados, la documentacion interactiva del servicio y el
  aviso del asesor con su servicio apagado.
- **El fuente `.drawio` del modelo fisico no esta versionado.** Solo esta su exportacion a
  PNG, de modo que la figura no es reproducible desde el repositorio.
- **No hay imagen del diagrama de Ishikawa.** El analisis causal vive en prosa en el
  Capitulo 2 de la tesis.
