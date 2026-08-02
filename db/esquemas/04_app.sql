-- =============================================================================
-- ESQUEMA app — TRANSACCIONAL WEB
-- =============================================================================

CREATE TABLE IF NOT EXISTS app.rol (
    rol_id          SMALLINT PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE
);

INSERT INTO app.rol VALUES
    (1, 'Sostenedor'),
    (2, 'Director'),
    (3, 'Jefe UTP')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS app.sostenedor (
    sostenedor_id   SERIAL PRIMARY KEY,
    rut             TEXT UNIQUE,
    nombre          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app.usuario (
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
CREATE TABLE IF NOT EXISTS app.usuario_establecimiento (
    usuario_id      INTEGER NOT NULL REFERENCES app.usuario(usuario_id) ON DELETE CASCADE,
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    PRIMARY KEY (usuario_id, rbd)
);

-- Escenario "what-if" guardado por el directivo
CREATE TABLE IF NOT EXISTS app.simulacion (
    simulacion_id   SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES app.usuario(usuario_id),
    rbd             INTEGER NOT NULL REFERENCES core.establecimiento(rbd),
    periodo_base_id INTEGER NOT NULL REFERENCES core.periodo(periodo_id),
    nombre          TEXT NOT NULL,
    creada_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_simulacion_usuario ON app.simulacion(usuario_id, creada_en DESC);

-- Variables movidas por el usuario en el simulador
CREATE TABLE IF NOT EXISTS app.simulacion_ajuste (
    simulacion_id   INTEGER NOT NULL REFERENCES app.simulacion(simulacion_id) ON DELETE CASCADE,
    feature         TEXT NOT NULL,
    valor_original  NUMERIC(12,4),
    valor_simulado  NUMERIC(12,4) NOT NULL,
    PRIMARY KEY (simulacion_id, feature)
);

-- Resultado del escenario: valor predicho de cada factor y el índice
CREATE TABLE IF NOT EXISTS app.simulacion_resultado (
    simulacion_id   INTEGER NOT NULL REFERENCES app.simulacion(simulacion_id) ON DELETE CASCADE,
    factor_cod      TEXT NOT NULL REFERENCES core.factor_sned(factor_cod),
    valor_base      NUMERIC(6,3),
    valor_simulado  NUMERIC(6,3),
    PRIMARY KEY (simulacion_id, factor_cod)
);

-- Auditoría de accesos (Ley N° 21.719, principio de trazabilidad)
CREATE TABLE IF NOT EXISTS app.auditoria (
    auditoria_id    BIGSERIAL PRIMARY KEY,
    usuario_id      INTEGER REFERENCES app.usuario(usuario_id),
    accion          TEXT NOT NULL,
    entidad         TEXT,
    entidad_id      TEXT,
    ip_origen       INET,
    ocurrido_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_auditoria_usuario ON app.auditoria(usuario_id, ocurrido_en DESC);
