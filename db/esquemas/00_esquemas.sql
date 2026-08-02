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
