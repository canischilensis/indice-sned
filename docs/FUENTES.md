# Fuentes de datos publicas integradas

Once fuentes consolidadas mediante llave estricta **RBD + anio**, con exclusion total
de identificadores personales (MRUN). El inventario canonico y ejecutable vive en
`quanta/q1_ingesta/fuentes.py`.

| Codigo | Fuente | Organismo | Periodicidad | Carpeta |
|--------|--------|-----------|--------------|---------|
| `simce` | Mediciones estandarizadas SIMCE | Agencia de Calidad de la Educacion | anual | `data/raw/simce/` |
| `idps` | Indicadores de Desarrollo Personal y Social | Agencia de Calidad de la Educacion | anual | `data/raw/idps/` |
| `sned` | Resultados oficiales del Indice SNED | MINEDUC | bianual | `data/raw/sned/` |
| `rendimiento` | Resumen de rendimiento por establecimiento | MINEDUC | anual | `data/raw/rendimiento/` |
| `matricula` | Resumen de matricula por unidad educativa | MINEDUC | anual | `data/raw/matricula/` |
| `sep` | Preferentes, prioritarios y beneficiarios SEP | MINEDUC | anual | `data/raw/sep/` |
| `ive` | Indice de Vulnerabilidad Escolar | JUNAEB | anual | `data/raw/ive/` |
| `personal` | Dotacion docente y asistentes de la educacion | MINEDUC | anual | `data/raw/personal/` |
| `pat` | Procesos administrativos | Superintendencia de Educacion | anual | `data/raw/pat/` |
| `denuncias` | Denuncias ciudadanas | Superintendencia de Educacion | anual | `data/raw/denuncias/` |
| `mediaciones` | Mediaciones escolares | Superintendencia de Educacion | anual | `data/raw/mediaciones/` |
| `desvinculacion` | Tasa de incidencia de desvinculacion | MINEDUC | anual | `data/raw/desvinculacion/` |

## Excepciones normativas aplicadas

- **SIMCE 2022** se excluye programaticamente: el retiro de consecuencias a esa medicion
  la vuelve incomparable con la serie previa.
- **2020 y 2021** no tienen medicion estandarizada (suspension por pandemia).
- Los eventos de la Superintendencia se acotan por la ventana temporal declarada en
  `catalogo.ventana_temporal`, no por conveniencia de calendario.

## Portales de origen

- Datos abiertos MINEDUC — <https://datosabiertos.mineduc.cl>
- Agencia de Calidad de la Educacion — <https://informacionpublica.agenciaeducacion.cl>
- Superintendencia de Educacion — <https://www.supereduc.cl>
- JUNAEB — <https://www.junaeb.cl>
