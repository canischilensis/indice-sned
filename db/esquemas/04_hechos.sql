-- ===========================================================================
-- 04 · Entidades debiles: lo observado
-- ---------------------------------------------------------------------------
-- Toda tabla de este esquema proviene de un rectangulo doble del diagrama y
-- por tanto tiene CLAVE PRIMARIA COMPUESTA que incluye la del padre (regla 9).
-- Las relaciones identificadoras (rombo doble) llevan ON DELETE CASCADE: una
-- entidad debil no puede existir sin su padre.
-- ===========================================================================

-- --- RESULTADO_SNED --------------------------------------------------------
-- `cluster_codigo` vive AQUI y no en `establecimiento` porque la relacion
-- GRUPO_HOMOGENEO --agrupa-- RESULTADO_SNED conecta con el resultado, no con
-- el establecimiento. Es la decision de modelado que resuelve el hallazgo del
-- 35,1 % de establecimientos que cambian de agrupacion entre ciclos.
--
-- `indicer` es atributo DERIVADO en el diagrama. Se almacena de todos modos
-- (opcion pragmatica) porque el valor oficial lo emite el Estado y se conserva
-- tal cual; la vista v_indicer_reconstruido existe para auditar que coincide
-- con la formula, no para reemplazarlo.
--
-- `posicion_en_grupo`, tambien derivado, NO se almacena: lo calcula la vista
-- v_ranking_intra_cluster.
CREATE TABLE IF NOT EXISTS hechos.sned_resultado (
    rbd            INTEGER      NOT NULL REFERENCES core.establecimiento(rbd) ON DELETE CASCADE,
    periodo_id     INTEGER      NOT NULL REFERENCES core.periodo(periodo_id),
    cluster_codigo INTEGER      REFERENCES core.grupo_homogeneo(cluster_codigo),
    indicer        NUMERIC(6,3),
    sel            SMALLINT,
    PRIMARY KEY (rbd, periodo_id)
);
COMMENT ON COLUMN hechos.sned_resultado.cluster_codigo IS
  'Indexado por periodo mediante la PK compuesta, NO como atributo invariante del establecimiento.';

-- --- VALOR_FACTOR ----------------------------------------------------------
-- Relacion identificadora 1:N con RESULTADO_SNED: la FK es compuesta y
-- arrastra el borrado en cascada.
CREATE TABLE IF NOT EXISTS hechos.sned_factor (
    rbd        INTEGER     NOT NULL,
    periodo_id INTEGER     NOT NULL,
    factor_cod VARCHAR(12) NOT NULL REFERENCES core.factor_sned(factor_cod),
    valor      NUMERIC(6,3),
    PRIMARY KEY (rbd, periodo_id, factor_cod),
    FOREIGN KEY (rbd, periodo_id)
        REFERENCES hechos.sned_resultado(rbd, periodo_id) ON DELETE CASCADE
);
COMMENT ON TABLE hechos.sned_factor IS
  'Rombo doble traducido literalmente: FK compuesta + ON DELETE CASCADE.';

-- --- MEDICION_SIMCE --------------------------------------------------------
-- Aqui ocurre la transformacion central del modelo: las ocho columnas anchas
-- del conjunto de entrenamiento (simce_lect_4b, simce_mate_4b, ...) se
-- convierten en filas. Un establecimiento que no imparte 2do medio simplemente
-- no tiene esas filas: desaparece el 68,7 % de nulos estructurales.
CREATE TABLE IF NOT EXISTS hechos.simce_medicion (
    rbd            INTEGER    NOT NULL REFERENCES core.establecimiento(rbd) ON DELETE CASCADE,
    periodo_id     INTEGER    NOT NULL REFERENCES core.periodo(periodo_id),
    nivel_cod      VARCHAR(4) NOT NULL REFERENCES core.nivel_educativo(nivel_cod),
    asignatura_cod VARCHAR(8) NOT NULL REFERENCES core.asignatura(asignatura_cod),
    anio_aplicacion SMALLINT,                 -- anio real de rendicion
    puntaje        NUMERIC(6,2),              -- opcional [O]: sin NOT NULL
    PRIMARY KEY (rbd, periodo_id, nivel_cod, asignatura_cod)
);
COMMENT ON COLUMN hechos.simce_medicion.anio_aplicacion IS
  'Anio real de rendicion. NO forma parte de la llave: se registra UNA sola '
  'aplicacion por periodo, nivel y asignatura, la que el SNED considera para el '
  'bienio. Esta columna deja constancia de cual fue, conservando la trazabilidad '
  'sin romper la simetria con idps_medicion ni la union en la matriz.';
COMMENT ON TABLE hechos.simce_medicion IS
  'La ausencia de fila significa que el establecimiento no imparte ese nivel. No es un nulo ambiguo.';

-- --- MEDICION_IDPS ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS hechos.idps_medicion (
    rbd           INTEGER    NOT NULL REFERENCES core.establecimiento(rbd) ON DELETE CASCADE,
    periodo_id    INTEGER    NOT NULL REFERENCES core.periodo(periodo_id),
    nivel_cod     VARCHAR(4) NOT NULL REFERENCES core.nivel_educativo(nivel_cod),
    dimension_cod VARCHAR(4) NOT NULL REFERENCES core.dimension_idps(dimension_cod),
    valor         NUMERIC(6,2),              -- opcional [O]: sin NOT NULL
    PRIMARY KEY (rbd, periodo_id, nivel_cod, dimension_cod)
);
COMMENT ON COLUMN hechos.idps_medicion.valor IS
  'Nomenclatura del Anexo de mapeo (Tabla A4): la medida de IDPS es `valor`, la de SIMCE `puntaje`.';

-- --- EVENTO_SIE ------------------------------------------------------------
-- Agregado por ventana temporal declarada, no por anio calendario: es la
-- ventana la que garantiza que no se filtren eventos posteriores al corte.
CREATE TABLE IF NOT EXISTS hechos.sie_evento_agregado (
    rbd             INTEGER     NOT NULL REFERENCES core.establecimiento(rbd) ON DELETE CASCADE,
    ventana_id      INTEGER     NOT NULL REFERENCES core.ventana_sie(ventana_id),
    tipo_evento_cod VARCHAR(32) NOT NULL REFERENCES core.tipo_evento_sie(tipo_evento_cod),
    conteo          INTEGER     NOT NULL DEFAULT 0 CHECK (conteo >= 0),
    tasa_por_matricula NUMERIC(8,5),
    PRIMARY KEY (rbd, ventana_id, tipo_evento_cod)
);

-- --- INDICADOR_ANUAL -------------------------------------------------------
-- Tabla generica con catalogo de tipos: incorporar una fuente nueva inserta
-- registros y no altera el esquema.
CREATE TABLE IF NOT EXISTS hechos.indicador_anual (
    rbd           INTEGER     NOT NULL REFERENCES core.establecimiento(rbd) ON DELETE CASCADE,
    anio          SMALLINT    NOT NULL,
    indicador_cod VARCHAR(48) NOT NULL REFERENCES core.tipo_indicador(indicador_cod),
    valor         NUMERIC(14,4),
    PRIMARY KEY (rbd, anio, indicador_cod)
);
COMMENT ON TABLE hechos.indicador_anual IS
  'Rendimiento, matricula, SEP, personal, IVE y vulnerabilidad unificados. Anadir una fuente = INSERT.';

-- --- Indices de apoyo ------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_simce_rbd_periodo   ON hechos.simce_medicion (rbd, periodo_id);
CREATE INDEX IF NOT EXISTS ix_idps_rbd_periodo    ON hechos.idps_medicion (rbd, periodo_id);
CREATE INDEX IF NOT EXISTS ix_sned_cluster        ON hechos.sned_resultado (periodo_id, cluster_codigo);
CREATE INDEX IF NOT EXISTS ix_indicador_anual_tipo ON hechos.indicador_anual (indicador_cod, anio);
