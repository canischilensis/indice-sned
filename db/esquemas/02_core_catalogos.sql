-- ===========================================================================
-- 02 · Catalogos de normalizacion
-- ---------------------------------------------------------------------------
-- El patron: cada atributo que en el ER era texto con valores repetidos
-- (nivel, asignatura, dimension, tipo de evento) pasa a ser una tabla de
-- catalogo mas una clave foranea. Evita repetir "4to Basico" veinte mil veces
-- y es lo que lleva el esquema a tercera forma normal.
--
-- Ninguno de estos catalogos aparece como entidad en el diagrama: surgen al
-- implementar. Se declaran como tales en el informe.
-- ===========================================================================

-- --- PERIODO: entidad fuerte del ER ---------------------------------------
-- El atributo `duracion` es DERIVADO (punteado en el diagrama): no se
-- almacena. Se calcula al consultar como (anio_fin - anio_inicio + 1).
CREATE TABLE IF NOT EXISTS core.periodo (
    periodo_id   INTEGER  PRIMARY KEY,
    etiqueta     TEXT     NOT NULL UNIQUE,     -- '2024-2025'
    anio_inicio  SMALLINT NOT NULL,
    anio_fin     SMALLINT NOT NULL,
    tipo         VARCHAR(24) NOT NULL DEFAULT 'bienio_premio'
                 CHECK (tipo IN ('bienio_premio','anio_medicion','ciclo_referencia')),
    CHECK (anio_fin >= anio_inicio)
);
COMMENT ON TABLE core.periodo IS
  'Entidad fuerte. El atributo derivado `duracion` no se materializa (regla 5).';

-- --- GRUPO_HOMOGENEO: entidad fuerte --------------------------------------
CREATE TABLE IF NOT EXISTS core.grupo_homogeneo (
    cluster_codigo INTEGER PRIMARY KEY,
    descripcion    TEXT,
    nivel_ensenanza TEXT
);
COMMENT ON TABLE core.grupo_homogeneo IS
  'Agrupacion oficial de comparacion. Se relaciona con RESULTADO_SNED, no con ESTABLECIMIENTO.';

-- --- FACTOR_SNED: entidad fuerte (catalogo de ponderaciones) --------------
CREATE TABLE IF NOT EXISTS core.factor_sned (
    factor_cod    VARCHAR(12)  PRIMARY KEY,
    nombre        TEXT         NOT NULL,
    ponderacion   NUMERIC(4,3) NOT NULL CHECK (ponderacion > 0 AND ponderacion <= 1),
    es_accionable BOOLEAN      NOT NULL DEFAULT TRUE,
    fuente_oficial TEXT,
    vigente_desde DATE         NOT NULL DEFAULT DATE '2026-01-01',
    vigente_hasta DATE,
    restriccion   TEXT,
    descripcion   TEXT
);
COMMENT ON TABLE core.factor_sned IS
  'Las ponderaciones oficiales son DATO, no codigo: un cambio normativo es un UPDATE.';
COMMENT ON COLUMN core.factor_sned.es_accionable IS
  'El establecimiento puede influir en los insumos del factor dentro del ciclo. '
  'Distinto de `restriccion`, que marca los factores acotados por informacion no publica.';
COMMENT ON COLUMN core.periodo.tipo IS
  'Naturaleza del periodo. El SNED premia por bienio, pero SIMCE se aplica anualmente.';

-- Trigger de integridad: las ponderaciones vigentes deben sumar exactamente 1,0.
CREATE OR REPLACE FUNCTION core.fn_validar_suma_ponderaciones()
RETURNS TRIGGER AS $$
DECLARE
    total NUMERIC(6,3);
BEGIN
    SELECT COALESCE(SUM(ponderacion), 0) INTO total
      FROM core.factor_sned
     WHERE vigente_hasta IS NULL;

    IF total <> 1.000 THEN
        RAISE EXCEPTION
          'Las ponderaciones vigentes suman %, se esperaba 1.000. La formula oficial quedaria invalidada.',
          total;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_suma_ponderaciones ON core.factor_sned;
CREATE CONSTRAINT TRIGGER trg_suma_ponderaciones
    AFTER INSERT OR UPDATE OR DELETE ON core.factor_sned
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION core.fn_validar_suma_ponderaciones();

-- --- Catalogos que normalizan atributos de texto repetido -----------------

CREATE TABLE IF NOT EXISTS core.dependencia (
    cod_depe2   SMALLINT PRIMARY KEY,
    nombre      TEXT     NOT NULL,
    recibe_sned BOOLEAN  NOT NULL DEFAULT TRUE
);
COMMENT ON COLUMN core.dependencia.recibe_sned IS
  'Regla de negocio en el esquema: el particular pagado no recibe subvencion y '
  'por tanto no participa del SNED. Filtrar por dato, no por condicional disperso.';

CREATE TABLE IF NOT EXISTS core.nivel_educativo (
    nivel_cod VARCHAR(4) PRIMARY KEY,        -- 4b, 6b, 8b, 2m
    nombre    TEXT       NOT NULL,
    orden     SMALLINT   NOT NULL
);

CREATE TABLE IF NOT EXISTS core.asignatura (
    asignatura_cod VARCHAR(8) PRIMARY KEY,   -- lect, mate
    nombre         TEXT       NOT NULL
);

CREATE TABLE IF NOT EXISTS core.dimension_idps (
    dimension_cod VARCHAR(4)  PRIMARY KEY,    -- am, cc, pf, hv
    id_oficial    VARCHAR(16),                -- codigo del organismo emisor
    nombre        TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS core.tipo_indicador (
    indicador_cod   VARCHAR(48) PRIMARY KEY,
    nombre          TEXT        NOT NULL,
    fuente          VARCHAR(24) NOT NULL,
    unidad          VARCHAR(24),
    factor_asociado VARCHAR(12) REFERENCES core.factor_sned(factor_cod),
    descripcion     TEXT
);
COMMENT ON COLUMN core.tipo_indicador.factor_asociado IS
  'Linaje de datos en el esquema: que factor del indice alimenta este indicador. '
  'NULL = variable de contexto que no alimenta ningun factor directamente.';

CREATE TABLE IF NOT EXISTS core.tipo_evento_sie (
    tipo_evento_cod VARCHAR(32) PRIMARY KEY,
    familia         VARCHAR(16) NOT NULL
                    CHECK (familia IN ('denuncia','proceso','mediacion')),
    nombre          TEXT        NOT NULL,
    factor_asociado VARCHAR(12) REFERENCES core.factor_sned(factor_cod),
    organismo       TEXT        NOT NULL DEFAULT 'Superintendencia de Educacion'
);
COMMENT ON COLUMN core.tipo_evento_sie.factor_asociado IS
  'Linaje: que factor del indice alimenta este tipo de evento.';

-- Codifica la regla anti-fuga en el esquema: una ventana declarada, con su
-- proposito, en lugar de un corte implicito dentro de un script (CTRL-02).
-- Ventana declarada, autonoma del bienio: codifica la particion temporal del
-- experimento (entrenamiento / validacion), no el periodo de premiacion. Los
-- eventos SIE se agregan por ventana, nunca por anio suelto.
--
-- `fecha_corte` se conserva ademas de `anio_fin` porque CTRL-02 se verifica con
-- precision de dia: un evento del 30 de diciembre y otro del 2 de enero caen en
-- ventanas distintas, y el anio solo no permite distinguirlos.
CREATE TABLE IF NOT EXISTS core.ventana_sie (
    ventana_id  INTEGER     PRIMARY KEY,
    etiqueta    TEXT        NOT NULL UNIQUE,
    anio_inicio SMALLINT    NOT NULL,
    anio_fin    SMALLINT    NOT NULL,
    fecha_corte DATE        NOT NULL,
    proposito   TEXT        NOT NULL,
    CHECK (anio_fin >= anio_inicio)
);
COMMENT ON TABLE core.ventana_sie IS
  'CTRL-02: la regla anti-fuga temporal queda estructuralmente imposible de saltar.';
