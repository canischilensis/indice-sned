-- ===========================================================================
-- 05 · Registro de modelos e inferencias — CTRL-05
-- ---------------------------------------------------------------------------
-- ESTE ESQUEMA NO PROVIENE DEL DIAGRAMA ENTIDAD-RELACION. Es infraestructura
-- de trazabilidad del algoritmo, no dominio del problema. Se declara asi en el
-- informe para que la correspondencia ER -> SQL siga siendo uno a uno.
-- ===========================================================================

CREATE TABLE IF NOT EXISTS ml.modelo (
    modelo_id         BIGSERIAL   PRIMARY KEY,
    codigo            VARCHAR(32) NOT NULL,      -- EFECTIVR, global_INDICER, ...
    version           VARCHAR(16) NOT NULL,
    arquitectura      VARCHAR(48) NOT NULL,
    archivo_artefacto TEXT        NOT NULL,
    version_datos     VARCHAR(32) NOT NULL,
    version_libreria  VARCHAR(32),               -- los .joblib estan acoplados a ella
    hiperparametros   JSONB       NOT NULL,
    metricas          JSONB       NOT NULL,
    entrenado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    vigente           BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (codigo, version)
);
COMMENT ON COLUMN ml.modelo.version_libreria IS
  'Hallazgo de la verificacion: un artefacto entrenado con scikit-learn 1.5.2 no carga con 1.8.';
COMMENT ON TABLE ml.modelo IS
  'Un modelo pasa a vigente solo si supera al anterior en R2 con prueba t pareada.';

-- Solo un modelo vigente por codigo.
CREATE UNIQUE INDEX IF NOT EXISTS ux_modelo_vigente
    ON ml.modelo (codigo) WHERE vigente;

CREATE TABLE IF NOT EXISTS ml.inferencia (
    inferencia_id  BIGSERIAL   PRIMARY KEY,
    modelo_id      BIGINT      NOT NULL REFERENCES ml.modelo(modelo_id),
    rbd            INTEGER     NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id     INTEGER     REFERENCES core.periodo(periodo_id),
    valor_estimado NUMERIC(6,3) NOT NULL,
    emitida_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_inferencia_rbd ON ml.inferencia (rbd, emitida_en DESC);

CREATE TABLE IF NOT EXISTS ml.explicacion (
    inferencia_id BIGINT        NOT NULL REFERENCES ml.inferencia(inferencia_id) ON DELETE CASCADE,
    variable      VARCHAR(64)   NOT NULL,
    valor         NUMERIC(14,4),
    contribucion  NUMERIC(10,5) NOT NULL,
    PRIMARY KEY (inferencia_id, variable)
);
COMMENT ON TABLE ml.explicacion IS
  'Valores de Shapley persistidos. Requisito declarado: 100 % de las inferencias desplegadas.';

CREATE TABLE IF NOT EXISTS ml.verificacion_bianual (
    verificacion_id BIGSERIAL   PRIMARY KEY,
    ejecutada_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    version_base    VARCHAR(32) NOT NULL,
    n_con_deriva    SMALLINT    NOT NULL,
    recomendacion   TEXT        NOT NULL,
    decision_humana TEXT,
    reporte         JSONB       NOT NULL
);
COMMENT ON TABLE ml.verificacion_bianual IS
  'CTRL-03: el reentrenamiento se AUTORIZA, no se dispara automaticamente.';
