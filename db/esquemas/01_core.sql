-- =============================================================================
-- ESQUEMA core — DIMENSIONES Y CATÁLOGOS
-- =============================================================================

-- Jerarquía geográfica oficial (códigos SUBDERE)
CREATE TABLE IF NOT EXISTS core.region (
    cod_region      SMALLINT PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS core.provincia (
    cod_provincia   SMALLINT PRIMARY KEY,
    cod_region      SMALLINT NOT NULL REFERENCES core.region(cod_region),
    nombre          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS core.comuna (
    cod_comuna      INTEGER PRIMARY KEY,
    cod_provincia   SMALLINT NOT NULL REFERENCES core.provincia(cod_provincia),
    nombre          TEXT NOT NULL
);

-- Dependencia administrativa (COD_DEPE2 del MINEDUC)
CREATE TABLE IF NOT EXISTS core.dependencia (
    cod_depe2       SMALLINT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    recibe_sned     BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO core.dependencia (cod_depe2, nombre, recibe_sned) VALUES
    (1, 'Municipal',                      TRUE),
    (2, 'Particular Subvencionado',       TRUE),
    (3, 'Particular Pagado',              FALSE),
    (4, 'Corporación Administración Delegada (DL 3166)', TRUE),
    (5, 'Servicio Local de Educación',    TRUE)
ON CONFLICT DO NOTHING;

-- Establecimiento: solo atributos INVARIANTES en el tiempo.
-- Los atributos que cambian (dependencia, ruralidad) viven en
-- establecimiento_periodo, como dimensión de cambio lento tipo 2.
CREATE TABLE IF NOT EXISTS core.establecimiento (
    rbd             INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL,
    cod_comuna      INTEGER REFERENCES core.comuna(cod_comuna),
    CONSTRAINT ck_rbd_positivo CHECK (rbd > 0)
);

CREATE INDEX IF NOT EXISTS ix_establecimiento_comuna ON core.establecimiento(cod_comuna);

-- Periodo: unifica bienios SIMCE/IDPS y ciclos de premio SNED.
-- El campo 'tipo' evita mezclar ventanas que no son comparables.
CREATE TABLE IF NOT EXISTS core.periodo (
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
    ('CICLO_SNED',      '2024-25', 2024, 2025)
ON CONFLICT DO NOTHING;

-- Atributos del establecimiento que varían por periodo.
-- Necesario porque la migración Municipal -> SLE altera la dependencia
-- sin cambiar el RBD; sobrescribirla falsearía los ciclos históricos.
CREATE TABLE IF NOT EXISTS core.establecimiento_periodo (
    rbd             INTEGER  NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_id      INTEGER  NOT NULL REFERENCES core.periodo(periodo_id),
    cod_depe2       SMALLINT REFERENCES core.dependencia(cod_depe2),
    es_rural        BOOLEAN,
    PRIMARY KEY (rbd, periodo_id)
);

-- Niveles evaluados
CREATE TABLE IF NOT EXISTS core.nivel_educativo (
    nivel_cod       TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    orden           SMALLINT NOT NULL
);

INSERT INTO core.nivel_educativo VALUES
    ('4b', '4° Básico',  1),
    ('6b', '6° Básico',  2),
    ('8b', '8° Básico',  3),
    ('2m', 'II Medio',   4)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS core.asignatura (
    asignatura_cod  TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL
);

INSERT INTO core.asignatura VALUES
    ('LECT', 'Comprensión de Lectura'),
    ('MATE', 'Matemática')
ON CONFLICT DO NOTHING;

-- Dimensiones IDPS. El mapeo numérico corresponde al id_indicador de la
-- glosa oficial 2025: 1=AM, 2=CC, 3=PF, 4=HV (nótese que 3 y 4 NO siguen
-- el orden alfabético; verificado contra la glosa de la Agencia de Calidad).
CREATE TABLE IF NOT EXISTS core.dimension_idps (
    dimension_cod   TEXT PRIMARY KEY,
    id_oficial      SMALLINT NOT NULL UNIQUE,
    nombre          TEXT NOT NULL
);

INSERT INTO core.dimension_idps VALUES
    ('AM', 1, 'Autoestima Académica y Motivación Escolar'),
    ('CC', 2, 'Clima de Convivencia Escolar'),
    ('PF', 3, 'Participación y Formación Ciudadana'),
    ('HV', 4, 'Hábitos de Vida Saludable')
ON CONFLICT DO NOTHING;

-- Catálogo de los seis factores con su ponderación legal.
-- La fórmula del índice queda como DATO, no incrustada en el código.
-- Verificado empíricamente: reconstruye INDICER con R²=1,0000 y MAE=0,000.
CREATE TABLE IF NOT EXISTS core.factor_sned (
    factor_cod      TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    ponderacion     NUMERIC(4,3) NOT NULL CHECK (ponderacion BETWEEN 0 AND 1),
    fuente_oficial  TEXT NOT NULL,
    es_accionable   BOOLEAN NOT NULL,
    vigente_desde   SMALLINT NOT NULL DEFAULT 2016,
    vigente_hasta   SMALLINT,
    descripcion     TEXT,
    restriccion     TEXT
);

-- `restriccion` carga la frontera de información irreducible: el subconjunto
-- de la fórmula que el organismo emisor no publica. Es hallazgo de la tesis,
-- no detalle de implementación.
INSERT INTO core.factor_sned
    (factor_cod, nombre, ponderacion, fuente_oficial, es_accionable, descripcion, restriccion) VALUES
    ('EFECTIVR', 'Efectividad',                     0.370, 'SIMCE', TRUE,
     'Resultados de las mediciones estandarizadas por nivel y asignatura.', NULL),
    ('SUPERAR',  'Superación',                      0.280, 'SIMCE (diferencias con corrección de significancia)', TRUE,
     'Avance respecto de la medición del bienio anterior.',
     'Corrección por significancia estadística no pública'),
    ('IGUALDR',  'Igualdad de Oportunidades',       0.220, 'Rendimiento MINEDUC + Superintendencia + PIE', TRUE,
     'Retención, aprobación, no discriminación e integración de estudiantes vulnerables.',
     'Subtipo de sanción por discriminación no desagregado'),
    ('INICIAR',  'Iniciativa',                      0.060, 'Ficha SNED (no pública)', TRUE,
     'Capacidad de incorporar innovaciones y comprometer apoyo externo.',
     'Ficha SNED de autorreporte, no pública'),
    ('INTEGRAR', 'Integración y Participación',     0.050, 'Ficha SNED (no pública)', TRUE,
     'Participación de la comunidad escolar y convivencia.',
     'Ficha SNED de autorreporte, no pública'),
    ('MEJORAR',  'Mejoramiento de las Condiciones', 0.020, 'Procesos administrativos sancionatorios', TRUE,
     'Cumplimiento normativo y condiciones de trabajo.',
     'Varianza del objetivo próxima a cero')
ON CONFLICT DO NOTHING;

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

DROP TRIGGER IF EXISTS tg_valida_ponderaciones ON core.factor_sned;
CREATE CONSTRAINT TRIGGER tg_valida_ponderaciones
    AFTER INSERT OR UPDATE OR DELETE ON core.factor_sned
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION core.valida_ponderaciones();

-- Grupos homogéneos oficiales. Se CONSUMEN del Estado, no se recalculan
-- (Objetivo Específico 2: descartar la programación de clustering propio).
CREATE TABLE IF NOT EXISTS core.grupo_homogeneo (
    cluster_codigo  INTEGER PRIMARY KEY,
    descripcion     TEXT,
    nivel_ensenanza TEXT
);

-- Catálogo de indicadores anuales de contexto (rendimiento, matrícula,
-- SEP, personal, IVE). Diseño genérico: sumar una fuente nueva es insertar
-- un registro aquí, no alterar el esquema.
CREATE TABLE IF NOT EXISTS core.tipo_indicador (
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
    ('IVE_CONSOLIDADO',  'IVE-SINAE consolidado',         'JUNAEB',                 'proporcion', NULL)
ON CONFLICT DO NOTHING;

-- Tipos de evento de la Superintendencia de Educación
CREATE TABLE IF NOT EXISTS core.tipo_evento_sie (
    tipo_evento_cod TEXT PRIMARY KEY,
    familia         TEXT NOT NULL
                    CHECK (familia IN ('DENUNCIA', 'PROCESO', 'MEDIACION')),
    nombre          TEXT NOT NULL,
    factor_asociado TEXT REFERENCES core.factor_sned(factor_cod),
    organismo       TEXT NOT NULL DEFAULT 'Superintendencia de Educación'
);

INSERT INTO core.tipo_evento_sie
    (tipo_evento_cod, familia, nombre, factor_asociado) VALUES
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
    ('MED_DE_DENUNCIA','MEDIACION', 'Mediaciones originadas en denuncia',   NULL)
ON CONFLICT DO NOTHING;

-- Ventanas temporales de agregación de eventos SIE.
-- Codifica en el esquema la regla anti-fuga: los eventos deben ser
-- ANTERIORES a la ventana de medición del ciclo que se predice.
-- `fecha_corte` conserva la precisión de día que fija el documento oficial
-- del proceso SNED (p. ej. procesos administrativos hasta el 30/06/2025).
CREATE TABLE IF NOT EXISTS core.ventana_sie (
    ventana_id      SERIAL PRIMARY KEY,
    etiqueta        TEXT NOT NULL UNIQUE,
    anio_inicio     SMALLINT NOT NULL,
    anio_fin        SMALLINT NOT NULL,
    fecha_corte     DATE,
    proposito       TEXT NOT NULL
                    CHECK (proposito IN ('ENTRENAMIENTO', 'VALIDACION', 'INFERENCIA')),
    CONSTRAINT ck_ventana_orden CHECK (anio_fin >= anio_inicio)
);

INSERT INTO core.ventana_sie (etiqueta, anio_inicio, anio_fin, fecha_corte, proposito) VALUES
    ('2016-2017', 2016, 2017, DATE '2017-12-31', 'ENTRENAMIENTO'),
    ('2018-2022', 2018, 2022, DATE '2022-12-31', 'VALIDACION')
ON CONFLICT DO NOTHING;
