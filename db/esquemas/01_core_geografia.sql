-- ===========================================================================
-- 01 · Jerarquia geografica
-- ---------------------------------------------------------------------------
-- COMUNA aparece en el diagrama como entidad fuerte. Region y provincia son
-- descomposicion de la jerarquia geografica implicita en ella: no estaban en el
-- ER y se agregan al implementar, para evitar repetir el nombre de la region en
-- cada comuna (normalizacion a 3FN).
-- ===========================================================================

CREATE TABLE IF NOT EXISTS core.region (
    cod_region   SMALLINT     PRIMARY KEY,
    nombre       TEXT         NOT NULL,
    orden_norte_sur SMALLINT
);

CREATE TABLE IF NOT EXISTS core.provincia (
    cod_provincia INTEGER   PRIMARY KEY,
    cod_region    SMALLINT  NOT NULL REFERENCES core.region(cod_region),
    nombre        TEXT      NOT NULL
);

CREATE TABLE IF NOT EXISTS core.comuna (
    cod_comuna    INTEGER   PRIMARY KEY,   -- atributo subrayado del ER -> PK
    cod_provincia INTEGER   REFERENCES core.provincia(cod_provincia),
    nombre        TEXT      NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_comuna_provincia ON core.comuna (cod_provincia);
COMMENT ON TABLE core.comuna IS 'Entidad fuerte del ER. Regla 1: entidad fuerte -> tabla.';
