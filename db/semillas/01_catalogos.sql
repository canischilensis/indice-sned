-- ===========================================================================
-- Semillas de los catalogos de normalizacion
-- ---------------------------------------------------------------------------
-- Idempotente: ON CONFLICT DO UPDATE.
--
-- IMPORTANTE: este archivo se aplica DESPUES de sembrar core.factor_sned,
-- porque tipo_indicador y tipo_evento_sie declaran `factor_asociado` con clave
-- foranea hacia el. El orden lo garantiza scripts/inicializar_bd.py.
--
-- Sobre `factor_asociado`: es el linaje de datos llevado al esquema. Los
-- valores asignados aqui son un primer mapeo fundado en la documentacion del
-- proyecto (la restriccion de IGUALDR menciona la desagregacion de sanciones;
-- MEJORAR corresponde a condiciones de trabajo). Los indicadores de contexto
-- puro quedan en NULL. Ajustar un mapeo es un UPDATE, no un despliegue.
-- ===========================================================================

INSERT INTO core.nivel_educativo (nivel_cod, nombre, orden) VALUES
    ('4b', '4to Basico',  1),
    ('6b', '6to Basico',  2),
    ('8b', '8vo Basico',  3),
    ('2m', '2do Medio',   4)
ON CONFLICT (nivel_cod) DO UPDATE SET nombre = EXCLUDED.nombre;

INSERT INTO core.asignatura (asignatura_cod, nombre) VALUES
    ('lect', 'Lectura'),
    ('mate', 'Matematica')
ON CONFLICT (asignatura_cod) DO UPDATE SET nombre = EXCLUDED.nombre;

INSERT INTO core.dimension_idps (dimension_cod, id_oficial, nombre) VALUES
    ('am', 'IDPS_AM', 'Autoestima academica y motivacion escolar'),
    ('cc', 'IDPS_CC', 'Clima de convivencia escolar'),
    ('pf', 'IDPS_PF', 'Participacion y formacion ciudadana'),
    ('hv', 'IDPS_HV', 'Habitos de vida saludable')
ON CONFLICT (dimension_cod) DO UPDATE
    SET nombre = EXCLUDED.nombre, id_oficial = EXCLUDED.id_oficial;

-- El particular pagado no recibe subvencion: no participa del SNED.
INSERT INTO core.dependencia (cod_depe2, nombre, recibe_sned) VALUES
    (1, 'Municipal',                              TRUE),
    (2, 'Particular subvencionado',               TRUE),
    (3, 'Particular pagado',                      FALSE),
    (4, 'Corporacion de administracion delegada', TRUE),
    (5, 'Servicio Local de Educacion Publica',    TRUE)
ON CONFLICT (cod_depe2) DO UPDATE
    SET nombre = EXCLUDED.nombre, recibe_sned = EXCLUDED.recibe_sned;

INSERT INTO core.tipo_evento_sie (tipo_evento_cod, familia, nombre, factor_asociado) VALUES
    ('denuncia_total',          'denuncia',  'Denuncias totales',                        'IGUALDR'),
    ('denuncia_fiscalizacion',  'denuncia',  'Denuncias derivadas a fiscalizacion',      'IGUALDR'),
    ('denuncia_juridica',       'denuncia',  'Denuncias con derivacion juridica',        'IGUALDR'),
    ('denuncia_ciberbullying',  'denuncia',  'Denuncias por ciberacoso',                 'IGUALDR'),
    ('proceso_total',           'proceso',   'Procesos administrativos',                 'IGUALDR'),
    ('proceso_con_sancion',     'proceso',   'Procesos con sancion',                     'IGUALDR'),
    ('proceso_multa',           'proceso',   'Procesos con multa',                       'IGUALDR'),
    ('proceso_priv_subvencion', 'proceso',   'Procesos con privacion de subvencion',     'IGUALDR'),
    ('mediacion_total',         'mediacion', 'Mediaciones',                               NULL),
    ('mediacion_efectiva',      'mediacion', 'Mediaciones efectivas',                     NULL),
    ('mediacion_de_denuncia',   'mediacion', 'Mediaciones originadas en denuncia',        NULL)
ON CONFLICT (tipo_evento_cod) DO UPDATE
    SET familia = EXCLUDED.familia,
        nombre = EXCLUDED.nombre,
        factor_asociado = EXCLUDED.factor_asociado;

INSERT INTO core.tipo_indicador (indicador_cod, nombre, fuente, unidad, factor_asociado, descripcion) VALUES
    ('tasa_aprobacion',     'Tasa de aprobacion',        'rendimiento', 'proporcion', 'EFECTIVR', 'Estudiantes aprobados sobre matricula final'),
    ('tasa_reprobacion',    'Tasa de reprobacion',       'rendimiento', 'proporcion', 'EFECTIVR', 'Estudiantes reprobados sobre matricula final'),
    ('tasa_retiro',         'Tasa de retiro',            'rendimiento', 'proporcion', 'IGUALDR',  'Estudiantes retirados sobre matricula inicial'),
    ('matricula_total',     'Matricula total',           'matricula',   'conteo',      NULL,      'Matricula total del establecimiento'),
    ('cursos_total',        'Cursos',                    'matricula',   'conteo',      NULL,      'Numero de cursos'),
    ('n_vulnerables',       'Estudiantes prioritarios',  'sep',         'conteo',     'IGUALDR',  'Estudiantes prioritarios'),
    ('n_beneficiarios_sep', 'Beneficiarios SEP',         'sep',         'conteo',     'IGUALDR',  'Beneficiarios de la subvencion preferencial'),
    ('tiene_convenio_sep',  'Convenio SEP vigente',      'sep',         'booleano',   'IGUALDR',  'Convenio SEP vigente'),
    ('n_docentes',          'Dotacion docente',          'personal',    'conteo',     'MEJORAR',  'Dotacion docente'),
    ('horas_docentes',      'Horas docentes',            'personal',    'horas',      'MEJORAR',  'Horas docentes contratadas'),
    ('n_directivos',        'Equipo directivo',          'personal',    'conteo',     'MEJORAR',  'Equipo directivo'),
    ('n_asistentes',        'Asistentes de la educacion','personal',    'conteo',     'MEJORAR',  'Asistentes de la educacion'),
    ('ive_basica',          'IVE basica',                'ive',         'proporcion', 'IGUALDR',  'Indice de vulnerabilidad, ensenanza basica'),
    ('ive_media',           'IVE media',                 'ive',         'proporcion', 'IGUALDR',  'Indice de vulnerabilidad, ensenanza media'),
    ('ive_consolidado',     'IVE consolidado',           'ive',         'proporcion', 'IGUALDR',  'Indice de vulnerabilidad consolidado')
ON CONFLICT (indicador_cod) DO UPDATE
    SET nombre = EXCLUDED.nombre,
        factor_asociado = EXCLUDED.factor_asociado,
        descripcion = EXCLUDED.descripcion;
