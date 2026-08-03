# Paridad entre adaptadores del puerto `RepositorioEstablecimientos`

El patrón Repository promete que la capa de servicio no sabe de dónde viene el dato.
Aquí eso se verifica, no se afirma: las mismas llamadas contra parquet y contra PostgreSQL
deben devolver lo mismo, campo por campo.

## Qué hay aquí

| Archivo | Qué es |
|---------|--------|
| `muestra.py` / `muestra.json` | Muestra fija de 20 RBD con semilla `20260802`, incluidos cuatro casos borde |
| `arnes.py` | Ejercita los 7 endpoints y congela las respuestas |
| `baseline_parquet/` | Respuestas del adaptador de parquet |
| `resultado_postgres/` | Respuestas del adaptador de PostgreSQL |
| `test_paridad_adaptadores.py` | La comparación, ejecutable en CI |

## Correr la comparación

No necesita PostgreSQL ni artefactos: compara las respuestas ya congeladas.

```bash
pytest -m paridad
```

Por eso corre en CI y falla si alguien rompe la paridad más adelante.

## Regenerar las respuestas

Esto sí necesita la base cargada y los seis artefactos.

```bash
REPOSITORIO_DATOS=parquet  python tests/paridad/arnes.py baseline_parquet
REPOSITORIO_DATOS=postgres python tests/paridad/arnes.py resultado_postgres
```

## Criterios de aceptación

Numéricos con tolerancia de 0,001, y 0,0001 estricto en los campos que la base guarda con
tres decimales o más (`indicer`, `ponderacion`, `aporte_al_indice`). Texto y categóricos
idénticos. Listas ordenadas con el mismo orden y los mismos elementos. Donde uno devuelve
nulo el otro debe devolver nulo: no se acepta que uno dé 0 y el otro `null`.

## Exclusiones, con su razón

**`ranking`** — la paridad es imposible por construcción, no por defecto: la base rankea sobre
los 11.569 RBD de los 5 ciclos y el parquet sobre los 7.754 del conjunto depurado en 3. Son
poblaciones distintas compitiendo dentro del mismo cluster.

**`cod_depe2`** — el parquet trae la dependencia de la ventana de features 2018-19 y la base
la trae por ciclo. Un establecimiento que migró de Municipal a SLEP aparece con valores
distintos y ambos son correctos para su período.

**`nom_rbd`** — el parquet lo trae truncado a 40 caracteres y sin tildes. Manda la base.

**`origen`** — es el nombre del adaptador activo: metadato, no dato.

**Los seis factores y `SEL`** — son el objetivo del modelo; exponerlos como variable de
entrada sería fuga.

## Una lección que costó

La primera versión de esta prueba comparaba que ambos adaptadores devolvieran **lo mismo**,
pero no que devolvieran **éxito**. El endpoint `shapley` fallaba con 422 en los dos y la
comparación lo daba por verde. De ahí viene
`test_todas_las_llamadas_son_exitosas`: comparar igualdad sin exigir éxito deja pasar
endpoints caídos.
