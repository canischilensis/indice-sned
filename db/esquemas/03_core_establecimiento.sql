-- ===========================================================================
-- 03 · ESTABLECIMIENTO y su relacion con PERIODO
-- ===========================================================================

-- --- Entidad fuerte: rectangulo simple del ER -----------------------------
-- `rbd` subrayado -> PRIMARY KEY (regla 3).
-- `cod_comuna` NO era atributo en el diagrama: aparece porque la relacion
-- COMUNA (1) --ubica-- (N) ESTABLECIMIENTO obliga a que la clave del lado "1"
-- viaje como FOREIGN KEY al lado "N" (regla 7).
--
-- Nota sobre el tipo del RBD. Se almacena como INTEGER, que es su forma
-- canonica. La ingesta lo LEE como texto para no perder ceros a la izquierda
-- durante el parseo y recien despues lo normaliza: son dos etapas distintas y
-- ambas necesarias. Ver quanta/q1_ingesta/calidad.py::normalizar_rbd.
CREATE TABLE IF NOT EXISTS core.establecimiento (
    rbd        INTEGER PRIMARY KEY,
    nombre     TEXT    NOT NULL,
    cod_comuna INTEGER REFERENCES core.comuna(cod_comuna),
    fecha_alta DATE,
    fecha_baja DATE,
    CHECK (fecha_baja IS NULL OR fecha_baja >= fecha_alta)
);
COMMENT ON COLUMN core.establecimiento.fecha_baja IS
  'Ciclo de vida del establecimiento. Explica por que un RBD desaparece entre '
  'bienios sin que sea un error de cruce: el establecimiento cerro.';
COMMENT ON TABLE core.establecimiento IS
  'Entidad fuerte del ER. El atributo compuesto `nombre_completo` no se materializa: se conserva solo `nombre`.';

-- --- Entidad asociativa: resuelve la M:N ESTABLECIMIENTO <-> PERIODO ------
-- Traduccion clasica de un muchos-a-muchos: tabla intermedia cuya PK es la
-- concatenacion de las dos claves, mas los atributos propios de la relacion
-- (regla 8).
--
-- Esta tabla es ademas la dimension de cambio lento: la dependencia
-- administrativa varia cuando un establecimiento migra a un Servicio Local de
-- Educacion, sin que cambie su RBD. Almacenarla como atributo invariante de
-- ESTABLECIMIENTO falsearia los ciclos historicos.
CREATE TABLE IF NOT EXISTS core.establecimiento_periodo (
    rbd        INTEGER  NOT NULL REFERENCES core.establecimiento(rbd) ON DELETE CASCADE,
    periodo_id INTEGER  NOT NULL REFERENCES core.periodo(periodo_id),
    cod_depe2  SMALLINT REFERENCES core.dependencia(cod_depe2),   -- opcional [O]
    es_rural   BOOLEAN,                                            -- opcional [O]
    PRIMARY KEY (rbd, periodo_id)
);
COMMENT ON TABLE core.establecimiento_periodo IS
  'Entidad asociativa (M:N) y dimension de cambio lento. Atributos opcionales sin NOT NULL.';

CREATE INDEX IF NOT EXISTS ix_est_periodo_periodo ON core.establecimiento_periodo (periodo_id);
