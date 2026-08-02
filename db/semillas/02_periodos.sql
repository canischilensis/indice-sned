-- ===========================================================================
-- Periodos de premiacion y ventanas temporales
-- ---------------------------------------------------------------------------
-- `duracion` es atributo derivado: NO se almacena. Se obtiene como
--     (anio_fin - anio_inicio + 1)
-- ===========================================================================

INSERT INTO core.periodo (periodo_id, etiqueta, anio_inicio, anio_fin, tipo) VALUES
    (1, '2016-2017', 2016, 2017, 'bienio_premio'),
    (2, '2018-2019', 2018, 2019, 'bienio_premio'),
    (3, '2020-2021', 2020, 2021, 'bienio_premio'),
    (4, '2022-2023', 2022, 2023, 'bienio_premio'),
    (5, '2024-2025', 2024, 2025, 'bienio_premio')
ON CONFLICT (periodo_id) DO UPDATE
    SET etiqueta = EXCLUDED.etiqueta,
        anio_inicio = EXCLUDED.anio_inicio,
        anio_fin = EXCLUDED.anio_fin,
        tipo = EXCLUDED.tipo;

-- Ventanas SIE: particion temporal del experimento, NO el bienio de premiacion.
-- Los eventos de la Superintendencia se agregan por ventana declarada, de modo
-- que ningun evento posterior al corte puede filtrarse al conjunto de
-- entrenamiento (CTRL-02).
INSERT INTO core.ventana_sie (ventana_id, etiqueta, anio_inicio, anio_fin, fecha_corte, proposito) VALUES
    (1, 'SIE 2016-2017', 2016, 2017, DATE '2017-12-31', 'Entrenamiento: eventos anteriores al corte de ajuste del modelo'),
    (2, 'SIE 2018-2022', 2018, 2022, DATE '2022-12-31', 'Validacion: eventos posteriores al ajuste, nunca vistos por el modelo')
ON CONFLICT (ventana_id) DO UPDATE
    SET etiqueta = EXCLUDED.etiqueta,
        anio_inicio = EXCLUDED.anio_inicio,
        anio_fin = EXCLUDED.anio_fin,
        fecha_corte = EXCLUDED.fecha_corte,
        proposito = EXCLUDED.proposito;
