-- ===========================================================================
-- 00 · Espacios logicos
-- ---------------------------------------------------------------------------
-- Cuatro esquemas. Los dos primeros derivan del modelo conceptual (diagrama
-- entidad-relacion); los dos ultimos son infraestructura y NO provienen del ER,
-- distincion que conviene declarar explicitamente en el informe.
-- ===========================================================================

CREATE SCHEMA IF NOT EXISTS core;    -- entidades fuertes y catalogos del dominio
CREATE SCHEMA IF NOT EXISTS hechos;  -- entidades debiles: lo observado
CREATE SCHEMA IF NOT EXISTS ml;      -- registro de modelos e inferencias
CREATE SCHEMA IF NOT EXISTS app;     -- transaccional de aplicacion

COMMENT ON SCHEMA core   IS 'Derivado del ER: entidades fuertes, entidad asociativa y catalogos de normalizacion a 3FN.';
COMMENT ON SCHEMA hechos IS 'Derivado del ER: entidades debiles con clave compuesta. Formato largo.';
COMMENT ON SCHEMA ml     IS 'No proviene del ER. Infraestructura de trazabilidad del algoritmo (CTRL-05).';
COMMENT ON SCHEMA app    IS 'No proviene del ER. RBAC, simulaciones y auditoria de acceso (CTRL-04).';
