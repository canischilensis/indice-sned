-- =============================================================================
-- ESQUEMA ml — REGISTRO DE MODELOS E INFERENCIAS
-- =============================================================================

CREATE TABLE IF NOT EXISTS ml.algoritmo (
    algoritmo_cod   TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    libreria        TEXT NOT NULL,
    familia         TEXT NOT NULL
);

INSERT INTO ml.algoritmo VALUES
    ('RF',    'Random Forest Regressor',              'scikit-learn', 'BAGGING'),
    ('HGB',   'HistGradientBoosting Regressor',       'scikit-learn', 'BOOSTING'),
    ('MLP',   'Perceptrón Multicapa',                 'keras',        'RED_NEURONAL')
ON CONFLICT DO NOTHING;

-- Un registro por modelo entrenado y versionado (Model Registry)
CREATE TABLE IF NOT EXISTS ml.modelo (
    modelo_id           SERIAL PRIMARY KEY,
    nombre              TEXT NOT NULL,
    alcance             TEXT NOT NULL CHECK (alcance IN ('FACTOR', 'GLOBAL')),
    factor_cod          TEXT REFERENCES core.factor_sned(factor_cod),
    algoritmo_cod       TEXT NOT NULL REFERENCES ml.algoritmo(algoritmo_cod),
    version             TEXT NOT NULL,
    fecha_entrenamiento TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ruta_artefacto      TEXT NOT NULL,
    n_observaciones     INTEGER,
    n_grupos            INTEGER,
    esquema_validacion  TEXT DEFAULT 'GroupKFold(5) por RBD',
    en_produccion       BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (nombre, version),
    CONSTRAINT ck_factor_segun_alcance CHECK (
        (alcance = 'FACTOR' AND factor_cod IS NOT NULL) OR
        (alcance = 'GLOBAL' AND factor_cod IS NULL)
    )
);

-- Un solo modelo global en producción a la vez
CREATE UNIQUE INDEX IF NOT EXISTS ux_modelo_global_produccion
    ON ml.modelo(alcance) WHERE alcance = 'GLOBAL' AND en_produccion;

-- Un solo modelo por factor en producción a la vez
CREATE UNIQUE INDEX IF NOT EXISTS ux_modelo_factor_produccion
    ON ml.modelo(factor_cod) WHERE alcance = 'FACTOR' AND en_produccion;

CREATE TABLE IF NOT EXISTS ml.modelo_metrica (
    modelo_id       INTEGER NOT NULL REFERENCES ml.modelo(modelo_id) ON DELETE CASCADE,
    metrica_cod     TEXT NOT NULL CHECK (metrica_cod IN ('R2','MAE','RMSE','R2_IC_INF','R2_IC_SUP')),
    valor           NUMERIC(10,5) NOT NULL,
    PRIMARY KEY (modelo_id, metrica_cod)
);

CREATE TABLE IF NOT EXISTS ml.modelo_hiperparametro (
    modelo_id       INTEGER NOT NULL REFERENCES ml.modelo(modelo_id) ON DELETE CASCADE,
    nombre          TEXT NOT NULL,
    valor           TEXT NOT NULL,
    PRIMARY KEY (modelo_id, nombre)
);

-- Features que consume cada modelo, con su mediana de imputación.
-- El simulador necesita esta tabla para construir el vector de entrada
-- y para saber qué controles habilitar en la interfaz.
CREATE TABLE IF NOT EXISTS ml.modelo_feature (
    modelo_id           INTEGER NOT NULL REFERENCES ml.modelo(modelo_id) ON DELETE CASCADE,
    feature             TEXT NOT NULL,
    orden               SMALLINT NOT NULL,
    mediana_imputacion  NUMERIC(12,4),
    es_manipulable      BOOLEAN NOT NULL DEFAULT FALSE,
    valor_min           NUMERIC(12,4),
    valor_max           NUMERIC(12,4),
    PRIMARY KEY (modelo_id, feature)
);

-- Registro histórico de inferencias (trazabilidad y monitoreo de drift)
CREATE TABLE IF NOT EXISTS ml.inferencia (
    inferencia_id   BIGSERIAL PRIMARY KEY,
    modelo_id       INTEGER NOT NULL REFERENCES ml.modelo(modelo_id),
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    valor_predicho  NUMERIC(6,3) NOT NULL,
    generada_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_inferencia_rbd ON ml.inferencia(rbd, periodo_id);

-- Atribución SHAP por variable (explicabilidad local del Reporte XAI)
CREATE TABLE IF NOT EXISTS ml.inferencia_atribucion (
    inferencia_id   BIGINT NOT NULL REFERENCES ml.inferencia(inferencia_id) ON DELETE CASCADE,
    feature         TEXT NOT NULL,
    shap_valor      NUMERIC(10,5) NOT NULL,
    PRIMARY KEY (inferencia_id, feature)
);

-- Monitoreo de Data Drift entre ingestas (PSI)
CREATE TABLE IF NOT EXISTS ml.drift_registro (
    drift_id        SERIAL PRIMARY KEY,
    feature         TEXT NOT NULL,
    periodo_base_id INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    periodo_nuevo_id INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    psi             NUMERIC(8,5) NOT NULL,
    supera_umbral   BOOLEAN GENERATED ALWAYS AS (psi > 0.2) STORED,
    evaluado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
