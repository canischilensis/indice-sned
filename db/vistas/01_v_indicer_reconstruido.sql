-- ===========================================================================
-- Vista 1 · Auditoria del atributo derivado `indicer`
-- ---------------------------------------------------------------------------
-- `indicer` esta punteado en el diagrama (derivado). Se adopto la opcion
-- pragmatica: almacenarlo, porque el valor oficial lo emite el Estado y se
-- conserva tal cual, y usar esta vista para AUDITAR que coincide con la formula
-- reconstruida a partir de los factores y sus ponderaciones.
--
-- El control empirico arrojo R2 = 1,0000 y MAE = 0,000: la formula publicada
-- reproduce el indice ministerial sin ajustes no declarados. Si la discrepancia
-- deja de ser cero, cambio la normativa o el catalogo de ponderaciones.
-- ===========================================================================

-- Nomenclatura alineada con el SQL citado en el Anexo de mapeo (seccion 4.1):
-- `indicer_calculado`, `indicer_oficial` y `discrepancia` en valor absoluto.
-- Se agregan tres columnas de apoyo que el Anexo no declara y que no alteran
-- las anteriores: el signo de la desviacion, la etiqueta del periodo y el
-- conteo de factores (control de completitud: deben ser siempre seis).
CREATE OR REPLACE VIEW hechos.v_indicer_reconstruido AS
SELECT
    sf.rbd,
    sf.periodo_id,
    ROUND(SUM(sf.valor * f.ponderacion), 3)                  AS indicer_calculado,
    sr.indicer                                               AS indicer_oficial,
    ROUND(ABS(SUM(sf.valor * f.ponderacion) - sr.indicer), 4) AS discrepancia,
    ROUND(SUM(sf.valor * f.ponderacion) - sr.indicer, 4)     AS discrepancia_con_signo,
    p.etiqueta                                               AS periodo,
    COUNT(*)                                                 AS n_factores
FROM hechos.sned_factor sf
JOIN core.factor_sned      f  ON f.factor_cod = sf.factor_cod
JOIN hechos.sned_resultado sr ON sr.rbd = sf.rbd AND sr.periodo_id = sf.periodo_id
JOIN core.periodo          p  ON p.periodo_id = sf.periodo_id
GROUP BY sf.rbd, sf.periodo_id, sr.indicer, p.etiqueta;

COMMENT ON VIEW hechos.v_indicer_reconstruido IS
  'Atributo derivado auditado, no recalculado. Discrepancia distinta de cero = alarma normativa.';
