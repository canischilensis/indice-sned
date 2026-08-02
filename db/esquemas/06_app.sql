-- ===========================================================================
-- 06 · Transaccional de aplicacion — CTRL-04
-- ---------------------------------------------------------------------------
-- Tampoco proviene del ER. Datos "calientes": alta concurrencia, baja latencia.
-- ===========================================================================

CREATE TABLE IF NOT EXISTS app.usuario (
    usuario_id BIGSERIAL   PRIMARY KEY,
    usuario    VARCHAR(64) UNIQUE NOT NULL,
    nombre     TEXT        NOT NULL,
    hash_clave TEXT        NOT NULL,
    rol        VARCHAR(16) NOT NULL CHECK (rol IN ('sostenedor','directivo','auditor')),
    activo     BOOLEAN     NOT NULL DEFAULT TRUE,
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.jurisdiccion (
    usuario_id BIGINT  NOT NULL REFERENCES app.usuario(usuario_id) ON DELETE CASCADE,
    rbd        INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    PRIMARY KEY (usuario_id, rbd)
);
COMMENT ON TABLE app.jurisdiccion IS
  'Minimo privilegio: un director solo accede a los RBD bajo su jurisdiccion legal.';

CREATE TABLE IF NOT EXISTS app.simulacion (
    simulacion_id BIGSERIAL   PRIMARY KEY,
    usuario_id    BIGINT      NOT NULL REFERENCES app.usuario(usuario_id),
    rbd           INTEGER     NOT NULL REFERENCES core.establecimiento(rbd),
    variable      VARCHAR(64) NOT NULL,
    escenario     JSONB       NOT NULL,
    resultado     NUMERIC(6,3),
    ejecutada_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE app.simulacion IS
  'Las simulaciones no alteran los registros historicos: solo se registran.';

CREATE TABLE IF NOT EXISTS app.auditoria_acceso (
    auditoria_id BIGSERIAL   PRIMARY KEY,
    usuario_id   BIGINT      REFERENCES app.usuario(usuario_id),
    accion       VARCHAR(48) NOT NULL,
    rbd          INTEGER,
    permitido    BOOLEAN     NOT NULL,
    ocurrido_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE app.auditoria_acceso IS 'Registro inmutable exigido por CTRL-04.';
