-- =============================================================================
-- ESQUEMA hechos — DATOS OBSERVADOS
-- =============================================================================

-- Resultado SNED por establecimiento y ciclo.
-- El grupo homogéneo se almacena AQUÍ y no en la dimensión del
-- establecimiento: el 35,1% de los colegios cambia de cluster entre ciclos.
CREATE TABLE IF NOT EXISTS hechos.sned_resultado (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    cluster_codigo  INTEGER REFERENCES core.grupo_homogeneo(cluster_codigo),
    indicer         NUMERIC(6,3) CHECK (indicer BETWEEN 0 AND 100),
    sel             SMALLINT CHECK (sel IN (1, 2, 3)),
    PRIMARY KEY (rbd, periodo_id)
);

COMMENT ON COLUMN hechos.sned_resultado.sel IS
    '1 = seleccionado tramo 100%; 2 = seleccionado tramo 60%; 3 = no seleccionado';

CREATE INDEX IF NOT EXISTS ix_sned_periodo  ON hechos.sned_resultado(periodo_id);
CREATE INDEX IF NOT EXISTS ix_sned_cluster  ON hechos.sned_resultado(cluster_codigo, periodo_id);

-- Valor de cada factor. Formato largo: permite consultar la fórmula
-- mediante JOIN con core.factor_sned sin hardcodear las ponderaciones.
CREATE TABLE IF NOT EXISTS hechos.sned_factor (
    rbd             INTEGER NOT NULL,
    periodo_id      INTEGER NOT NULL,
    factor_cod      TEXT    NOT NULL REFERENCES core.factor_sned(factor_cod),
    -- float32 en origen: 6 decimales reproducen el valor exacto en la prueba
    -- de ida y vuelta sobre las 248.957 observaciones (diferencia 0,00e+00).
    valor           NUMERIC(9,6) CHECK (valor BETWEEN 0 AND 100),
    PRIMARY KEY (rbd, periodo_id, factor_cod),
    FOREIGN KEY (rbd, periodo_id)
        REFERENCES hechos.sned_resultado(rbd, periodo_id) ON DELETE CASCADE
);

-- Mediciones SIMCE en formato largo.
-- La ausencia de fila significa que el establecimiento no imparte ese
-- nivel: se elimina el 68,7% de nulos estructurales de la tabla ancha.
CREATE TABLE IF NOT EXISTS hechos.simce_medicion (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    nivel_cod       TEXT    NOT NULL REFERENCES core.nivel_educativo(nivel_cod),
    asignatura_cod  TEXT    NOT NULL REFERENCES core.asignatura(asignatura_cod),
    puntaje         NUMERIC(6,2) CHECK (puntaje BETWEEN 0 AND 400),
    PRIMARY KEY (rbd, periodo_id, nivel_cod, asignatura_cod)
);

CREATE INDEX IF NOT EXISTS ix_simce_periodo ON hechos.simce_medicion(periodo_id, nivel_cod);

-- Mediciones IDPS, misma lógica de formato largo
CREATE TABLE IF NOT EXISTS hechos.idps_medicion (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    nivel_cod       TEXT    NOT NULL REFERENCES core.nivel_educativo(nivel_cod),
    dimension_cod   TEXT    NOT NULL REFERENCES core.dimension_idps(dimension_cod),
    -- float32 en origen: 6 decimales reproducen el valor exacto en la prueba
    -- de ida y vuelta sobre las 248.957 observaciones (diferencia 0,00e+00).
    valor           NUMERIC(9,6) CHECK (valor BETWEEN 0 AND 100),
    PRIMARY KEY (rbd, periodo_id, nivel_cod, dimension_cod)
);

-- Eventos de la Superintendencia agregados por ventana temporal
CREATE TABLE IF NOT EXISTS hechos.sie_evento_agregado (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    ventana_id      INTEGER NOT NULL REFERENCES core.ventana_sie(ventana_id),
    tipo_evento_cod TEXT    NOT NULL REFERENCES core.tipo_evento_sie(tipo_evento_cod),
    conteo          INTEGER NOT NULL DEFAULT 0 CHECK (conteo >= 0),
    PRIMARY KEY (rbd, ventana_id, tipo_evento_cod)
);

CREATE INDEX IF NOT EXISTS ix_sie_ventana ON hechos.sie_evento_agregado(ventana_id, tipo_evento_cod);

-- Indicadores anuales de contexto (rendimiento, matrícula, SEP, personal, IVE)
-- NOTA DE DISEÑO: la clave usa periodo_id y NO un año calendario.
-- Los valores cargados corresponden al PROMEDIO de un bienio de medición
-- (p. ej. 2018 y 2019 promediados), construido así en los notebooks de ingesta.
-- Etiquetarlos con un año único declararía un dato que no existe.
CREATE TABLE IF NOT EXISTS hechos.indicador_anual (
    rbd             INTEGER  NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER  NOT NULL REFERENCES core.periodo(periodo_id),
    indicador_cod   TEXT     NOT NULL REFERENCES core.tipo_indicador(indicador_cod),
    -- float64 nativo: son cocientes de enteros y ninguna precision decimal los
    -- reproduce exacto. A 8 decimales el error maximo es 5e-9.
    valor           NUMERIC(14,8),
    PRIMARY KEY (rbd, periodo_id, indicador_cod)
);

CREATE INDEX IF NOT EXISTS ix_indicador_periodo ON hechos.indicador_anual(periodo_id, indicador_cod);
