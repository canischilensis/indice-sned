-- =============================================================================
-- BASE DE DATOS NORMALIZADA — SIMULADOR PREDICTIVO ÍNDICE SNED
-- PostgreSQL 14+
--
-- Arquitectura en cuatro esquemas, siguiendo la separación OLTP/OLAP
-- declarada en el diseño de solución de la tesis:
--
--   core    : dimensiones y catálogos normalizados (3FN)
--   hechos  : datos observados del Estado (repositorio analítico)
--   ml      : registro de modelos, métricas e inferencias (MLOps estático)
--   app     : transaccional web — usuarios, permisos, simulaciones, auditoría
--
-- Llave de integridad referencial: RBD + periodo, conforme a la regla de
-- negocio ministerial. No se almacena ningún identificador personal (MRUN),
-- en cumplimiento de la Ley N° 21.719 sobre Protección de Datos Personales.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS hechos;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS app;


-- =============================================================================
-- ESQUEMA core — DIMENSIONES Y CATÁLOGOS
-- =============================================================================

-- Jerarquía geográfica oficial (códigos SUBDERE)
CREATE TABLE core.region (
    cod_region      SMALLINT PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE
);

CREATE TABLE core.provincia (
    cod_provincia   SMALLINT PRIMARY KEY,
    cod_region      SMALLINT NOT NULL REFERENCES core.region(cod_region),
    nombre          TEXT NOT NULL
);

CREATE TABLE core.comuna (
    cod_comuna      INTEGER PRIMARY KEY,
    cod_provincia   SMALLINT NOT NULL REFERENCES core.provincia(cod_provincia),
    nombre          TEXT NOT NULL
);

-- Dependencia administrativa (COD_DEPE2 del MINEDUC)
CREATE TABLE core.dependencia (
    cod_depe2       SMALLINT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    recibe_sned     BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO core.dependencia (cod_depe2, nombre, recibe_sned) VALUES
    (1, 'Municipal',                      TRUE),
    (2, 'Particular Subvencionado',       TRUE),
    (3, 'Particular Pagado',              FALSE),
    (4, 'Corporación Administración Delegada (DL 3166)', TRUE),
    (5, 'Servicio Local de Educación',    TRUE);

-- Establecimiento: solo atributos INVARIANTES en el tiempo.
-- Los atributos que cambian (dependencia, ruralidad) viven en
-- establecimiento_periodo, como dimensión de cambio lento tipo 2.
CREATE TABLE core.establecimiento (
    rbd             INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL,
    cod_comuna      INTEGER REFERENCES core.comuna(cod_comuna),
    fecha_alta      DATE,
    fecha_baja      DATE,
    CONSTRAINT ck_rbd_positivo CHECK (rbd > 0)
);

CREATE INDEX ix_establecimiento_comuna ON core.establecimiento(cod_comuna);

-- Periodo: unifica bienios SIMCE/IDPS y ciclos de premio SNED.
-- El campo 'tipo' evita mezclar ventanas que no son comparables.
CREATE TABLE core.periodo (
    periodo_id      SERIAL PRIMARY KEY,
    tipo            TEXT NOT NULL
                    CHECK (tipo IN ('BIENIO_MEDICION', 'CICLO_SNED')),
    etiqueta        TEXT NOT NULL,
    anio_inicio     SMALLINT NOT NULL,
    anio_fin        SMALLINT NOT NULL,
    UNIQUE (tipo, etiqueta),
    CONSTRAINT ck_periodo_orden CHECK (anio_fin >= anio_inicio)
);

INSERT INTO core.periodo (tipo, etiqueta, anio_inicio, anio_fin) VALUES
    ('BIENIO_MEDICION', '2016-17', 2016, 2017),
    ('BIENIO_MEDICION', '2018-19', 2018, 2019),
    ('BIENIO_MEDICION', '2022-23', 2022, 2023),
    ('BIENIO_MEDICION', '2023-24', 2023, 2024),
    ('BIENIO_MEDICION', '2024-25', 2024, 2025),
    ('CICLO_SNED',      '2016-17', 2016, 2017),
    ('CICLO_SNED',      '2018-19', 2018, 2019),
    ('CICLO_SNED',      '2020-21', 2020, 2021),
    ('CICLO_SNED',      '2022-23', 2022, 2023),
    ('CICLO_SNED',      '2024-25', 2024, 2025);

-- Atributos del establecimiento que varían por periodo.
-- Necesario porque la migración Municipal -> SLE altera la dependencia
-- sin cambiar el RBD; sobrescribirla falsearía los ciclos históricos.
CREATE TABLE core.establecimiento_periodo (
    rbd             INTEGER  NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER  NOT NULL REFERENCES core.periodo(periodo_id),
    cod_depe2       SMALLINT REFERENCES core.dependencia(cod_depe2),
    es_rural        BOOLEAN,
    PRIMARY KEY (rbd, periodo_id)
);

-- Niveles evaluados
CREATE TABLE core.nivel_educativo (
    nivel_cod       TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    orden           SMALLINT NOT NULL
);

INSERT INTO core.nivel_educativo VALUES
    ('4b', '4° Básico',  1),
    ('6b', '6° Básico',  2),
    ('8b', '8° Básico',  3),
    ('2m', 'II Medio',   4);

CREATE TABLE core.asignatura (
    asignatura_cod  TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL
);

INSERT INTO core.asignatura VALUES
    ('LECT', 'Comprensión de Lectura'),
    ('MATE', 'Matemática');

-- Dimensiones IDPS. El mapeo numérico corresponde al id_indicador de la
-- glosa oficial 2025: 1=AM, 2=CC, 3=PF, 4=HV (nótese que 3 y 4 NO siguen
-- el orden alfabético; verificado contra la glosa de la Agencia de Calidad).
CREATE TABLE core.dimension_idps (
    dimension_cod   TEXT PRIMARY KEY,
    id_oficial      SMALLINT NOT NULL UNIQUE,
    nombre          TEXT NOT NULL
);

INSERT INTO core.dimension_idps VALUES
    ('AM', 1, 'Autoestima Académica y Motivación Escolar'),
    ('CC', 2, 'Clima de Convivencia Escolar'),
    ('PF', 3, 'Participación y Formación Ciudadana'),
    ('HV', 4, 'Hábitos de Vida Saludable');

-- Catálogo de los seis factores con su ponderación legal.
-- La fórmula del índice queda como DATO, no incrustada en el código.
-- Verificado empíricamente: reconstruye INDICER con R²=1,0000 y MAE=0,000.
CREATE TABLE core.factor_sned (
    factor_cod      TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    ponderacion     NUMERIC(4,3) NOT NULL CHECK (ponderacion BETWEEN 0 AND 1),
    fuente_oficial  TEXT NOT NULL,
    es_accionable   BOOLEAN NOT NULL,
    vigente_desde   SMALLINT NOT NULL DEFAULT 2016
);

INSERT INTO core.factor_sned
    (factor_cod, nombre, ponderacion, fuente_oficial, es_accionable) VALUES
    ('EFECTIVR', 'Efectividad',                     0.370, 'SIMCE', TRUE),
    ('SUPERAR',  'Superación',                      0.280, 'SIMCE (diferencias con corrección de significancia)', TRUE),
    ('IGUALDR',  'Igualdad de Oportunidades',       0.220, 'Rendimiento MINEDUC + Superintendencia + PIE', TRUE),
    ('INICIAR',  'Iniciativa',                      0.060, 'Ficha SNED (no pública)', TRUE),
    ('INTEGRAR', 'Integración y Participación',     0.050, 'Ficha SNED (no pública)', TRUE),
    ('MEJORAR',  'Mejoramiento de las Condiciones', 0.020, 'Procesos administrativos sancionatorios', TRUE);

-- Restricción de integridad de la fórmula: los pesos deben sumar 1
CREATE OR REPLACE FUNCTION core.valida_ponderaciones() RETURNS TRIGGER AS $$
DECLARE total NUMERIC;
BEGIN
    SELECT SUM(ponderacion) INTO total FROM core.factor_sned;
    IF ABS(total - 1.0) > 0.001 THEN
        RAISE EXCEPTION 'Las ponderaciones de factor_sned deben sumar 1.0 (suma actual: %)', total;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER tg_valida_ponderaciones
    AFTER INSERT OR UPDATE OR DELETE ON core.factor_sned
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION core.valida_ponderaciones();

-- Grupos homogéneos oficiales. Se CONSUMEN del Estado, no se recalculan
-- (Objetivo Específico 2: descartar la programación de clustering propio).
CREATE TABLE core.grupo_homogeneo (
    cluster_codigo  INTEGER PRIMARY KEY,
    descripcion     TEXT
);

-- Catálogo de indicadores anuales de contexto (rendimiento, matrícula,
-- SEP, personal, IVE). Diseño genérico: sumar una fuente nueva es insertar
-- un registro aquí, no alterar el esquema.
CREATE TABLE core.tipo_indicador (
    indicador_cod   TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    fuente          TEXT NOT NULL,
    unidad          TEXT NOT NULL,
    factor_asociado TEXT REFERENCES core.factor_sned(factor_cod)
);

INSERT INTO core.tipo_indicador
    (indicador_cod, nombre, fuente, unidad, factor_asociado) VALUES
    ('TASA_APROBACION',  'Tasa de aprobación',            'Resumen de Rendimiento', 'proporcion', 'IGUALDR'),
    ('TASA_REPROBACION', 'Tasa de reprobación',           'Resumen de Rendimiento', 'proporcion', 'IGUALDR'),
    ('TASA_RETIRO',      'Tasa de retiro',                'Resumen de Rendimiento', 'proporcion', 'IGUALDR'),
    ('MATRICULA_TOTAL',  'Matrícula total declarada',     'Resumen de Matrícula',   'conteo',     NULL),
    ('MATRICULA_REND',   'Matrícula base de cálculo de tasas', 'Resumen de Rendimiento', 'conteo', 'IGUALDR'),
    ('CURSOS_TOTAL',     'Cursos totales',                'Resumen de Matrícula',   'conteo',     NULL),
    ('N_VULNERABLES',    'Alumnos prioritarios y preferentes', 'SEP',               'conteo',     'IGUALDR'),
    ('N_BENEF_SEP',      'Beneficiarios SEP',             'SEP',                    'conteo',     'IGUALDR'),
    ('CONVENIO_SEP',     'Convenio SEP vigente',          'SEP',                    'binaria',    NULL),
    ('N_DOCENTES',       'Dotación docente',              'Dotación Docente',       'conteo',     'INICIAR'),
    ('HORAS_DOCENTES',   'Horas de contrato docente',     'Dotación Docente',       'horas',      'INICIAR'),
    ('N_DIRECTIVOS',     'Cargos directivos',             'Dotación Docente',       'conteo',     'INICIAR'),
    ('N_ASISTENTES',     'Asistentes de la educación',    'Resumen de Asistentes',  'conteo',     'INTEGRAR'),
    ('IVE_BASICA',       'IVE-SINAE Básica',              'JUNAEB',                 'proporcion', NULL),
    ('IVE_MEDIA',        'IVE-SINAE Media',               'JUNAEB',                 'proporcion', NULL),
    ('IVE_CONSOLIDADO',  'IVE-SINAE consolidado',         'JUNAEB',                 'proporcion', NULL);

-- Tipos de evento de la Superintendencia de Educación
CREATE TABLE core.tipo_evento_sie (
    tipo_evento_cod TEXT PRIMARY KEY,
    familia         TEXT NOT NULL
                    CHECK (familia IN ('DENUNCIA', 'PROCESO', 'MEDIACION')),
    nombre          TEXT NOT NULL,
    factor_asociado TEXT REFERENCES core.factor_sned(factor_cod)
);

INSERT INTO core.tipo_evento_sie VALUES
    ('DEN_TOTAL',      'DENUNCIA',  'Denuncias totales',                    NULL),
    ('DEN_FISC',       'DENUNCIA',  'Derivadas a Fiscalización',            NULL),
    ('DEN_JURID',      'DENUNCIA',  'Derivadas a Unidad Jurídica',          'MEJORAR'),
    ('DEN_CIBER',      'DENUNCIA',  'Relacionadas con ciberbullying',       'INTEGRAR'),
    ('PA_TOTAL',       'PROCESO',   'Procesos administrativos terminados',  'MEJORAR'),
    ('PA_SANCION',     'PROCESO',   'Procesos con sanción',                 'MEJORAR'),
    ('PA_MULTA',       'PROCESO',   'Procesos con multa',                   'MEJORAR'),
    ('PA_PRIVACION',   'PROCESO',   'Privación de subvención',              'IGUALDR'),
    ('MED_TOTAL',      'MEDIACION', 'Solicitudes de mediación',             NULL),
    ('MED_EFECTIVA',   'MEDIACION', 'Mediaciones resueltas con/sin acuerdo','INTEGRAR'),
    ('MED_DE_DENUNCIA','MEDIACION', 'Mediaciones originadas en denuncia',   NULL);

-- Ventanas temporales de agregación de eventos SIE.
-- Codifica en el esquema la regla anti-fuga: los eventos deben ser
-- ANTERIORES a la ventana de medición del ciclo que se predice.
CREATE TABLE core.ventana_sie (
    ventana_id      SERIAL PRIMARY KEY,
    etiqueta        TEXT NOT NULL UNIQUE,
    anio_inicio     SMALLINT NOT NULL,
    anio_fin        SMALLINT NOT NULL,
    proposito       TEXT NOT NULL
                    CHECK (proposito IN ('ENTRENAMIENTO', 'VALIDACION', 'INFERENCIA')),
    CONSTRAINT ck_ventana_orden CHECK (anio_fin >= anio_inicio)
);

INSERT INTO core.ventana_sie (etiqueta, anio_inicio, anio_fin, proposito) VALUES
    ('2016-2017', 2016, 2017, 'ENTRENAMIENTO'),
    ('2018-2022', 2018, 2022, 'VALIDACION');


-- =============================================================================
-- ESQUEMA hechos — DATOS OBSERVADOS
-- =============================================================================

-- Resultado SNED por establecimiento y ciclo.
-- El grupo homogéneo se almacena AQUÍ y no en la dimensión del
-- establecimiento: el 35,1% de los colegios cambia de cluster entre ciclos.
CREATE TABLE hechos.sned_resultado (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    cluster_codigo  INTEGER REFERENCES core.grupo_homogeneo(cluster_codigo),
    indicer         NUMERIC(6,3) CHECK (indicer BETWEEN 0 AND 100),
    sel             SMALLINT CHECK (sel IN (1, 2, 3)),
    PRIMARY KEY (rbd, periodo_id)
);

COMMENT ON COLUMN hechos.sned_resultado.sel IS
    '1 = seleccionado tramo 100%; 2 = seleccionado tramo 60%; 3 = no seleccionado';

CREATE INDEX ix_sned_periodo  ON hechos.sned_resultado(periodo_id);
CREATE INDEX ix_sned_cluster  ON hechos.sned_resultado(cluster_codigo, periodo_id);

-- Valor de cada factor. Formato largo: permite consultar la fórmula
-- mediante JOIN con core.factor_sned sin hardcodear las ponderaciones.
CREATE TABLE hechos.sned_factor (
    rbd             INTEGER NOT NULL,
    periodo_id      INTEGER NOT NULL,
    factor_cod      TEXT    NOT NULL REFERENCES core.factor_sned(factor_cod),
    valor           NUMERIC(6,3) CHECK (valor BETWEEN 0 AND 100),
    PRIMARY KEY (rbd, periodo_id, factor_cod),
    FOREIGN KEY (rbd, periodo_id)
        REFERENCES hechos.sned_resultado(rbd, periodo_id) ON DELETE CASCADE
);

-- Mediciones SIMCE en formato largo.
-- La ausencia de fila significa que el establecimiento no imparte ese
-- nivel: se elimina el 68,7% de nulos estructurales de la tabla ancha.
CREATE TABLE hechos.simce_medicion (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    nivel_cod       TEXT    NOT NULL REFERENCES core.nivel_educativo(nivel_cod),
    asignatura_cod  TEXT    NOT NULL REFERENCES core.asignatura(asignatura_cod),
    anio_aplicacion SMALLINT NOT NULL,
    puntaje         NUMERIC(6,2) CHECK (puntaje BETWEEN 0 AND 400),
    PRIMARY KEY (rbd, periodo_id, nivel_cod, asignatura_cod)
);

CREATE INDEX ix_simce_periodo ON hechos.simce_medicion(periodo_id, nivel_cod);

-- Mediciones IDPS, misma lógica de formato largo
CREATE TABLE hechos.idps_medicion (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    nivel_cod       TEXT    NOT NULL REFERENCES core.nivel_educativo(nivel_cod),
    dimension_cod   TEXT    NOT NULL REFERENCES core.dimension_idps(dimension_cod),
    valor           NUMERIC(6,2) CHECK (valor BETWEEN 0 AND 100),
    PRIMARY KEY (rbd, periodo_id, nivel_cod, dimension_cod)
);

-- Eventos de la Superintendencia agregados por ventana temporal
CREATE TABLE hechos.sie_evento_agregado (
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    ventana_id      INTEGER NOT NULL REFERENCES core.ventana_sie(ventana_id),
    tipo_evento_cod TEXT    NOT NULL REFERENCES core.tipo_evento_sie(tipo_evento_cod),
    conteo          INTEGER NOT NULL DEFAULT 0 CHECK (conteo >= 0),
    PRIMARY KEY (rbd, ventana_id, tipo_evento_cod)
);

CREATE INDEX ix_sie_ventana ON hechos.sie_evento_agregado(ventana_id, tipo_evento_cod);

-- Indicadores anuales de contexto (rendimiento, matrícula, SEP, personal, IVE)
-- NOTA DE DISEÑO: la clave usa periodo_id y NO un año calendario.
-- Los valores cargados corresponden al PROMEDIO de un bienio de medición
-- (p. ej. 2018 y 2019 promediados), construido así en los notebooks de ingesta.
-- Etiquetarlos con un año único declararía un dato que no existe.
CREATE TABLE hechos.indicador_anual (
    rbd             INTEGER  NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER  NOT NULL REFERENCES core.periodo(periodo_id),
    indicador_cod   TEXT     NOT NULL REFERENCES core.tipo_indicador(indicador_cod),
    valor           NUMERIC(12,4),
    PRIMARY KEY (rbd, periodo_id, indicador_cod)
);

CREATE INDEX ix_indicador_periodo ON hechos.indicador_anual(periodo_id, indicador_cod);


-- =============================================================================
-- ESQUEMA ml — REGISTRO DE MODELOS E INFERENCIAS
-- =============================================================================

CREATE TABLE ml.algoritmo (
    algoritmo_cod   TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    libreria        TEXT NOT NULL,
    familia         TEXT NOT NULL
);

INSERT INTO ml.algoritmo VALUES
    ('RF',    'Random Forest Regressor',              'scikit-learn', 'BAGGING'),
    ('HGB',   'HistGradientBoosting Regressor',       'scikit-learn', 'BOOSTING'),
    ('MLP',   'Perceptrón Multicapa',                 'keras',        'RED_NEURONAL');

-- Un registro por modelo entrenado y versionado (Model Registry)
CREATE TABLE ml.modelo (
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
CREATE UNIQUE INDEX ux_modelo_global_produccion
    ON ml.modelo(alcance) WHERE alcance = 'GLOBAL' AND en_produccion;

-- Un solo modelo por factor en producción a la vez
CREATE UNIQUE INDEX ux_modelo_factor_produccion
    ON ml.modelo(factor_cod) WHERE alcance = 'FACTOR' AND en_produccion;

CREATE TABLE ml.modelo_metrica (
    modelo_id       INTEGER NOT NULL REFERENCES ml.modelo(modelo_id) ON DELETE CASCADE,
    metrica_cod     TEXT NOT NULL CHECK (metrica_cod IN ('R2','MAE','RMSE','R2_IC_INF','R2_IC_SUP')),
    valor           NUMERIC(10,5) NOT NULL,
    PRIMARY KEY (modelo_id, metrica_cod)
);

CREATE TABLE ml.modelo_hiperparametro (
    modelo_id       INTEGER NOT NULL REFERENCES ml.modelo(modelo_id) ON DELETE CASCADE,
    nombre          TEXT NOT NULL,
    valor           TEXT NOT NULL,
    PRIMARY KEY (modelo_id, nombre)
);

-- Features que consume cada modelo, con su mediana de imputación.
-- El simulador necesita esta tabla para construir el vector de entrada
-- y para saber qué controles habilitar en la interfaz.
CREATE TABLE ml.modelo_feature (
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
CREATE TABLE ml.inferencia (
    inferencia_id   BIGSERIAL PRIMARY KEY,
    modelo_id       INTEGER NOT NULL REFERENCES ml.modelo(modelo_id),
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    valor_predicho  NUMERIC(6,3) NOT NULL,
    generada_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_inferencia_rbd ON ml.inferencia(rbd, periodo_id);

-- Atribución SHAP por variable (explicabilidad local del Reporte XAI)
CREATE TABLE ml.inferencia_atribucion (
    inferencia_id   BIGINT NOT NULL REFERENCES ml.inferencia(inferencia_id) ON DELETE CASCADE,
    feature         TEXT NOT NULL,
    shap_valor      NUMERIC(10,5) NOT NULL,
    PRIMARY KEY (inferencia_id, feature)
);

-- Monitoreo de Data Drift entre ingestas (PSI)
CREATE TABLE ml.drift_registro (
    drift_id        SERIAL PRIMARY KEY,
    feature         TEXT NOT NULL,
    periodo_base_id INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    periodo_nuevo_id INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    psi             NUMERIC(8,5) NOT NULL,
    supera_umbral   BOOLEAN GENERATED ALWAYS AS (psi > 0.2) STORED,
    evaluado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- ESQUEMA app — TRANSACCIONAL WEB
-- =============================================================================

CREATE TABLE app.rol (
    rol_id          SMALLINT PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE
);

INSERT INTO app.rol VALUES
    (1, 'Sostenedor'),
    (2, 'Director'),
    (3, 'Jefe UTP');

CREATE TABLE app.sostenedor (
    sostenedor_id   SERIAL PRIMARY KEY,
    rut             TEXT UNIQUE,
    nombre          TEXT NOT NULL
);

CREATE TABLE app.usuario (
    usuario_id      SERIAL PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    nombre          TEXT NOT NULL,
    sostenedor_id   INTEGER REFERENCES app.sostenedor(sostenedor_id),
    rol_id          SMALLINT NOT NULL REFERENCES app.rol(rol_id),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultimo_acceso   TIMESTAMPTZ
);

-- Control de acceso: qué establecimientos puede consultar cada usuario
CREATE TABLE app.usuario_establecimiento (
    usuario_id      INTEGER NOT NULL REFERENCES app.usuario(usuario_id) ON DELETE CASCADE,
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    PRIMARY KEY (usuario_id, rbd)
);

-- Escenario "what-if" guardado por el directivo
CREATE TABLE app.simulacion (
    simulacion_id   SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES app.usuario(usuario_id),
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_base_id INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    nombre          TEXT NOT NULL,
    creada_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_simulacion_usuario ON app.simulacion(usuario_id, creada_en DESC);

-- Variables movidas por el usuario en el simulador
CREATE TABLE app.simulacion_ajuste (
    simulacion_id   INTEGER NOT NULL REFERENCES app.simulacion(simulacion_id) ON DELETE CASCADE,
    feature         TEXT NOT NULL,
    valor_original  NUMERIC(12,4),
    valor_simulado  NUMERIC(12,4) NOT NULL,
    PRIMARY KEY (simulacion_id, feature)
);

-- Resultado del escenario: valor predicho de cada factor y el índice
CREATE TABLE app.simulacion_resultado (
    simulacion_id   INTEGER NOT NULL REFERENCES app.simulacion(simulacion_id) ON DELETE CASCADE,
    factor_cod      TEXT NOT NULL REFERENCES core.factor_sned(factor_cod),
    valor_base      NUMERIC(6,3),
    valor_simulado  NUMERIC(6,3),
    PRIMARY KEY (simulacion_id, factor_cod)
);

-- Auditoría de accesos (Ley N° 21.719, principio de trazabilidad)
CREATE TABLE app.auditoria (
    auditoria_id    BIGSERIAL PRIMARY KEY,
    usuario_id      INTEGER REFERENCES app.usuario(usuario_id),
    accion          TEXT NOT NULL,
    entidad         TEXT,
    entidad_id      TEXT,
    ip_origen       INET,
    ocurrido_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_auditoria_usuario ON app.auditoria(usuario_id, ocurrido_en DESC);


-- =============================================================================
-- VISTAS DE CONSUMO
-- =============================================================================

-- Reconstrucción del INDICER desde los factores, usando las ponderaciones
-- almacenadas en el catálogo. Permite auditar cualquier discrepancia entre
-- el valor oficial y la fórmula declarada.
CREATE OR REPLACE VIEW hechos.v_indicer_reconstruido AS
SELECT
    sf.rbd,
    sf.periodo_id,
    ROUND(SUM(sf.valor * f.ponderacion), 3) AS indicer_calculado,
    sr.indicer                              AS indicer_oficial,
    ROUND(ABS(SUM(sf.valor * f.ponderacion) - sr.indicer), 4) AS discrepancia
FROM hechos.sned_factor sf
JOIN core.factor_sned   f  ON f.factor_cod = sf.factor_cod
JOIN hechos.sned_resultado sr
     ON sr.rbd = sf.rbd AND sr.periodo_id = sf.periodo_id
GROUP BY sf.rbd, sf.periodo_id, sr.indicer;

-- Posición del establecimiento dentro de su grupo homogéneo.
-- Es la mecánica real de la selección SNED: se compite dentro del cluster.
CREATE OR REPLACE VIEW hechos.v_ranking_intra_cluster AS
SELECT
    sr.rbd,
    sr.periodo_id,
    sr.cluster_codigo,
    sr.indicer,
    sr.sel,
    RANK()       OVER (PARTITION BY sr.periodo_id, sr.cluster_codigo
                       ORDER BY sr.indicer DESC) AS posicion,
    COUNT(*)     OVER (PARTITION BY sr.periodo_id, sr.cluster_codigo) AS n_grupo,
    PERCENT_RANK() OVER (PARTITION BY sr.periodo_id, sr.cluster_codigo
                         ORDER BY sr.indicer) AS percentil
FROM hechos.sned_resultado sr
WHERE sr.cluster_codigo IS NOT NULL;

-- Matriz ancha de entrenamiento, equivalente a tabla_modelo_largo.parquet.
-- Materializada porque el pivot es costoso y los datos son estáticos
-- (reentrenamiento bianual, no continuo).
CREATE MATERIALIZED VIEW ml.mv_matriz_entrenamiento AS
SELECT
    sr.rbd,
    p.etiqueta                                   AS ciclo_sned,
    sr.cluster_codigo,
    ep.cod_depe2,
    ep.es_rural,
    sr.indicer,
    sr.sel,
    MAX(CASE WHEN sm.nivel_cod='4b' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_4b,
    MAX(CASE WHEN sm.nivel_cod='4b' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_4b,
    MAX(CASE WHEN sm.nivel_cod='6b' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_6b,
    MAX(CASE WHEN sm.nivel_cod='6b' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_6b,
    MAX(CASE WHEN sm.nivel_cod='8b' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_8b,
    MAX(CASE WHEN sm.nivel_cod='8b' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_8b,
    MAX(CASE WHEN sm.nivel_cod='2m' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_2m,
    MAX(CASE WHEN sm.nivel_cod='2m' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_2m
FROM hechos.sned_resultado sr
JOIN core.periodo p  ON p.periodo_id = sr.periodo_id AND p.tipo = 'CICLO_SNED'
LEFT JOIN core.establecimiento_periodo ep
       ON ep.rbd = sr.rbd AND ep.periodo_id = sr.periodo_id
LEFT JOIN core.periodo pm
       ON pm.tipo = 'BIENIO_MEDICION' AND pm.etiqueta = '2018-19'
LEFT JOIN hechos.simce_medicion sm
       ON sm.rbd = sr.rbd AND sm.periodo_id = pm.periodo_id
WHERE p.etiqueta IN ('2020-21', '2022-23', '2024-25')
GROUP BY sr.rbd, p.etiqueta, sr.cluster_codigo, ep.cod_depe2,
         ep.es_rural, sr.indicer, sr.sel;

CREATE UNIQUE INDEX ux_mv_matriz ON ml.mv_matriz_entrenamiento(rbd, ciclo_sned);

-- Refrescar tras cada ciclo de ingesta:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY ml.mv_matriz_entrenamiento;
