# Datos

Ninguna carpeta de datos se versiona en git (ver `.gitignore`). El origen es publico
y re-descargable; lo que el repositorio garantiza es la **trazabilidad**, no la copia.

```
data/
├── raw/          Archivos originales del Estado, sin modificar. 12 carpetas por fuente.
├── interim/      Intermedios y CUARENTENA (CTRL-01): registros que no cruzaron la llave.
├── processed/    Parquet normalizado listo para el motor. Incluye _historico/ con las
│                 versiones intermedias de la tabla de modelamiento (v2 a v11).
└── external/     Datos de terceros no ministeriales.
```

## Invariantes

1. **El RBD se lee siempre como texto.** Leerlo como entero destruye los ceros a la izquierda
   y rompe silenciosamente el cruce entre fuentes.
2. **Nada se elimina.** Lo que no cruza va a `interim/cuarentena/` con motivo registrado.
3. **La ausencia es informacion.** Una fila ausente en formato largo significa que el
   establecimiento no imparte ese nivel; no es un nulo a imputar.
4. **Sin datos personales.** El MRUN queda excluido de toda ingesta por diseno.

## Verificar el inventario

```bash
python -m q1_ingesta.cli inventario
python -m q1_ingesta.cli verificar
```
