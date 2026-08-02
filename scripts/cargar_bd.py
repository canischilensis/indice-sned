"""Carga core, hechos y ml desde los parquet y JSON del proyecto.

    python scripts/cargar_bd.py

Requiere el esquema aplicado y DATABASE_URL. Idempotente: cada tabla se carga
por COPY a una temporal y de ahi con INSERT ... ON CONFLICT DO NOTHING.

Decisiones de carga declaradas:
  - cod_depe2 se carga TAL CUAL. core.dependencia tiene los cinco valores
    oficiales; no se recodifica nada.
  - Las features 2018-19 se repiten en las tres filas de ciclo de cada
    establecimiento: se deduplica y se carga una vez apuntando al
    BIENIO_MEDICION 2018-19.
  - simce_prom_4b y dif_simce_* NO se persisten: son derivadas.
  - No se fabrica anio_aplicacion: periodo_id ya codifica la ventana temporal.
  - core.conjunto_entrenamiento se puebla desde tabla_modelo_final_v11.parquet,
    que ya es el conjunto depurado de 7.754. El criterio no se reconstruye.
"""
import json, sys
import pandas as pd
from sqlalchemy import create_engine, text

import os
from pathlib import Path as _P
RAIZ = _P(__file__).resolve().parents[1]
B  = str(RAIZ / 'data' / 'processed') + '/'
MB = str(RAIZ / 'models' / 'metadata') + '/'
PERSONAL = str(RAIZ / 'data' / 'raw' / 'PERSONAL') + '/'
URL = os.getenv('DATABASE_URL')
if not URL:
    raise SystemExit('Falta DATABASE_URL. Copia .env.example a .env y completa la cadena.')
eng = create_engine(URL, future=True)
tot = {}

import io, time
def ins(cx, tabla, df, cols):
    """COPY a una tabla temporal y luego INSERT ... ON CONFLICT DO NOTHING.
    Rapido como COPY, idempotente como ON CONFLICT."""
    if df.empty: tot[tabla] = 0; return
    t0 = time.perf_counter()
    tmp = 'tmp_' + tabla.replace('.', '_')
    raw = cx.connection.dbapi_connection
    cur = raw.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {tmp}; CREATE TEMP TABLE {tmp} (LIKE {tabla} INCLUDING DEFAULTS)")
    buf = io.StringIO()
    df[cols].to_csv(buf, index=False, header=False, na_rep='\\N')
    buf.seek(0)
    cur.copy_expert(f"COPY {tmp} ({','.join(cols)}) FROM STDIN WITH (FORMAT csv, NULL '\\N')", buf)
    cur.execute(f"INSERT INTO {tabla} ({','.join(cols)}) SELECT {','.join(cols)} FROM {tmp} ON CONFLICT DO NOTHING")
    n = cur.rowcount
    cur.execute(f"DROP TABLE {tmp}")
    tot[tabla] = tot.get(tabla, 0) + n
    print(f"  {tabla:<34} {n:>8,}  ({time.perf_counter()-t0:.1f}s)", flush=True)

PROVINCIAS = {
 11:'Iquique', 14:'Tamarugal',
 21:'Antofagasta', 22:'El Loa', 23:'Tocopilla',
 31:'Copiapó', 32:'Chañaral', 33:'Huasco',
 41:'Elqui', 42:'Choapa', 43:'Limarí',
 51:'Valparaíso', 52:'Isla de Pascua', 53:'Los Andes', 54:'Petorca',
 55:'Quillota', 56:'San Antonio', 57:'San Felipe de Aconcagua', 58:'Marga Marga',
 61:'Cachapoal', 62:'Cardenal Caro', 63:'Colchagua',
 71:'Talca', 72:'Cauquenes', 73:'Curicó', 74:'Linares',
 81:'Concepción', 82:'Arauco', 83:'Biobío', 84:'Ñuble',
 91:'Cautín', 92:'Malleco',
 101:'Llanquihue', 102:'Chiloé', 103:'Osorno', 104:'Palena',
 111:'Coyhaique', 112:'Aysén', 113:'Capitán Prat', 114:'General Carrera',
 121:'Magallanes', 122:'Antártica Chilena', 123:'Tierra del Fuego',
 124:'Última Esperanza',
 131:'Santiago', 132:'Cordillera', 133:'Chacabuco', 134:'Maipo',
 135:'Melipilla', 136:'Talagante',
 141:'Valdivia', 142:'Ranco',
 151:'Arica', 152:'Parinacota',
 161:'Diguillín', 162:'Itata', 163:'Punilla',
}

def catalogo_comunas():
    """NOM_COM_RBD. sned_maestro_ciclos primero; si no la trae, dotacion docente.

    Se leen varios anios y se fusionan: el archivo 2018 es anterior a la
    creacion de la region de Nuble, de modo que sus 21 comunas solo aparecen
    en publicaciones posteriores.
    """
    import os, glob
    m = pd.read_parquet(B+'sned_maestro_ciclos.parquet')
    if 'NOM_COM_RBD' in m.columns:
        piezas = [m[['COD_COM_RBD','NOM_COM_RBD']]]
    else:
        piezas = []
        carpetas = [PERSONAL] + ([str(RAIZ/'data'/'raw'/'PERSONAL')+'/'] if RAIZ is not None else [])
        rutas = sorted({r for c in carpetas for r in glob.glob(c+'*ocenc*.csv') + glob.glob(c+'*ocent*.csv')})
        for ruta in rutas:
            # la codificacion cambia entre publicaciones: las antiguas son
            # latin-1 y las recientes utf-8. Leerlas todas como latin-1
            # produce mojibake en los nombres con tilde.
            for enc in ('utf-8', 'latin-1'):
                try:
                    piezas.append(pd.read_csv(ruta, sep=';', encoding=enc, low_memory=False,
                                              usecols=['COD_COM_RBD','NOM_COM_RBD']))
                    break
                except Exception:
                    continue
    if not piezas:
        return {}
    d = pd.concat(piezas, ignore_index=True).dropna().drop_duplicates('COD_COM_RBD')
    return dict(zip(d.COD_COM_RBD.astype(int), d.NOM_COM_RBD.astype(str).str.strip().str.title()))

REGIONES = {1:'Tarapacá',2:'Antofagasta',3:'Atacama',4:'Coquimbo',5:'Valparaíso',6:"O'Higgins",
            7:'Maule',8:'Biobío',9:'La Araucanía',10:'Los Lagos',11:'Aysén',12:'Magallanes',
            13:'Metropolitana',14:'Los Ríos',15:'Arica y Parinacota',16:'Ñuble'}

m = pd.read_parquet(B+'sned_maestro_ciclos.parquet')
m['RBD'] = m.RBD.astype(int)
L = pd.read_parquet(B+'tabla_modelo_largo.parquet'); L['rbd'] = L.rbd.astype(int)

with eng.begin() as cx:
    per = {(r[0], r[1]): r[2] for r in cx.execute(text("SELECT tipo, etiqueta, periodo_id FROM core.periodo")).all()}
    PM = per[('BIENIO_MEDICION', '2018-19')]        # ventana de medicion 2018-19
    ven = {r[0]: r[1] for r in cx.execute(text("SELECT etiqueta, ventana_id FROM core.ventana_sie")).all()}

    # ---------- core: geografia ----------
    reg = sorted(m.COD_REG_RBD.astype(int).unique())
    ins(cx, 'core.region', pd.DataFrame({'cod_region': reg,
        'nombre': [REGIONES.get(r, f'Región {r}') for r in reg]}), ['cod_region','nombre'])
    pr = m[['COD_PRO_RBD','COD_REG_RBD']].astype(int).drop_duplicates('COD_PRO_RBD')
    pr.columns = ['cod_provincia','cod_region']
    pr['nombre'] = pr.cod_provincia.map(lambda c: PROVINCIAS.get(c, f'Provincia {c}'))
    ins(cx, 'core.provincia', pr, ['cod_provincia','cod_region','nombre'])
    co = m[['COD_COM_RBD','COD_PRO_RBD']].astype(int).drop_duplicates('COD_COM_RBD')
    co.columns = ['cod_comuna','cod_provincia']
    NOMCOM = catalogo_comunas()
    co['nombre'] = co.cod_comuna.map(lambda c: NOMCOM.get(c, f'Comuna {c}'))
    ins(cx, 'core.comuna', co, ['cod_comuna','cod_provincia','nombre'])

    # ---------- core: establecimiento y grupo ----------
    est = m.sort_values('BIENIO_PREMIO').drop_duplicates('RBD', keep='last')
    est = pd.DataFrame({'rbd': est.RBD, 'nombre': est.NOM_RBD.fillna('SIN NOMBRE'),
                        'cod_comuna': est.COD_COM_RBD.astype(int)})
    ins(cx, 'core.establecimiento', est, ['rbd','nombre','cod_comuna'])
    ins(cx, 'core.grupo_homogeneo', pd.DataFrame({'cluster_codigo': sorted(m.CLUSTER.astype(int).unique())}),
        ['cluster_codigo'])

    # ---------- core: establecimiento_periodo ----------
    ep = m.copy(); ep['periodo_id'] = ep.BIENIO_PREMIO.astype(str).map(lambda e: per[('CICLO_SNED', e)])
    ep = ep.drop_duplicates(['RBD','periodo_id'])
    ep = pd.DataFrame({'rbd': ep.RBD, 'periodo_id': ep.periodo_id,
                       'cod_depe2': pd.to_numeric(ep.COD_DEPE2, errors='coerce'),
                       'es_rural': ep.ES_RURAL.astype('boolean')})
    ins(cx, 'core.establecimiento_periodo', ep, ['rbd','periodo_id','cod_depe2','es_rural'])

    # ---------- hechos: sned_resultado y sned_factor ----------
    sr = m.copy(); sr['periodo_id'] = sr.BIENIO_PREMIO.astype(str).map(lambda e: per[('CICLO_SNED', e)])
    sr = sr.drop_duplicates(['RBD','periodo_id'])
    ins(cx, 'hechos.sned_resultado', pd.DataFrame({'rbd': sr.RBD, 'periodo_id': sr.periodo_id,
        'cluster_codigo': sr.CLUSTER.astype(int), 'indicer': sr.INDICER, 'sel': sr.SEL.astype(int)}),
        ['rbd','periodo_id','cluster_codigo','indicer','sel'])
    F = ['EFECTIVR','SUPERAR','IGUALDR','INICIAR','INTEGRAR','MEJORAR']
    sf = sr.melt(id_vars=['RBD','periodo_id'], value_vars=F, var_name='factor_cod', value_name='valor').dropna(subset=['valor'])
    sf.columns = ['rbd','periodo_id','factor_cod','valor']
    ins(cx, 'hechos.sned_factor', sf, ['rbd','periodo_id','factor_cod','valor'])

    # ---------- hechos: SIMCE e IDPS (pivote inverso) ----------
    u = L.drop_duplicates('rbd')            # las features 2018-19 se repiten por ciclo
    sc = [c for c in u.columns if c.startswith('simce_') and c != 'simce_prom_4b']
    s = u.melt(id_vars='rbd', value_vars=sc, var_name='v', value_name='puntaje').dropna(subset=['puntaje'])
    s['asignatura_cod'] = s.v.str.split('_').str[1].str.upper()
    s['nivel_cod'] = s.v.str.split('_').str[2]
    s['periodo_id'] = PM
    ins(cx, 'hechos.simce_medicion', s, ['rbd','periodo_id','nivel_cod','asignatura_cod','puntaje'])

    ic = [c for c in u.columns if c.startswith('idps_')]
    i = u.melt(id_vars='rbd', value_vars=ic, var_name='v', value_name='valor').dropna(subset=['valor'])
    i['dimension_cod'] = i.v.str.split('_').str[1].str.upper()
    i['nivel_cod'] = i.v.str.split('_').str[2]; i['periodo_id'] = PM
    ins(cx, 'hechos.idps_medicion', i, ['rbd','periodo_id','nivel_cod','dimension_cod','valor'])

    # ---------- hechos: indicador_anual ----------
    MAPI = {'tasa_aprobacion':'TASA_APROBACION','tasa_reprobacion':'TASA_REPROBACION','tasa_retiro':'TASA_RETIRO',
            'matricula_total':'MATRICULA_TOTAL','total_matricula':'MATRICULA_REND','cursos_total':'CURSOS_TOTAL',
            'n_vulnerables':'N_VULNERABLES','n_beneficiarios_sep':'N_BENEF_SEP','tiene_convenio_sep':'CONVENIO_SEP',
            'n_docentes':'N_DOCENTES','horas_docentes':'HORAS_DOCENTES','n_directivos':'N_DIRECTIVOS',
            'n_asistentes':'N_ASISTENTES','ive_basica':'IVE_BASICA','ive_media':'IVE_MEDIA','ive_consolidado':'IVE_CONSOLIDADO'}
    ia = u.melt(id_vars='rbd', value_vars=list(MAPI), var_name='v', value_name='valor').dropna(subset=['valor'])
    ia['indicador_cod'] = ia.v.map(MAPI); ia['periodo_id'] = PM
    ia['valor'] = pd.to_numeric(ia.valor, errors='coerce'); ia = ia.dropna(subset=['valor'])
    ins(cx, 'hechos.indicador_anual', ia, ['rbd','periodo_id','indicador_cod','valor'])

    # ---------- hechos: eventos SIE, las dos ventanas ----------
    MAPE = {'denuncias_total':'DEN_TOTAL','denuncias_fiscalizacion':'DEN_FISC','denuncias_juridica':'DEN_JURID',
            'denuncias_ciberbullying':'DEN_CIBER','procesos_total':'PA_TOTAL','procesos_con_sancion':'PA_SANCION',
            'procesos_multa':'PA_MULTA','procesos_privacion_subvencion':'PA_PRIVACION','mediaciones_total':'MED_TOTAL',
            'mediaciones_efectivas':'MED_EFECTIVA','mediaciones_de_denuncia':'MED_DE_DENUNCIA'}
    validos = set(est.rbd)
    for etq, suf in [('2016-2017','2016_17'), ('2018-2022','2018_22')]:
        piezas = []
        for arch in [f'denuncias_{suf}_por_rbd.parquet', f'procesos_admin_{suf}_por_rbd.parquet', f'mediaciones_{suf}_por_rbd.parquet']:
            d = pd.read_parquet(B+arch); d['rbd'] = pd.to_numeric(d.rbd, errors='coerce')
            d = d.dropna(subset=['rbd']); d['rbd'] = d.rbd.astype(int)
            vv = [c for c in d.columns if c in MAPE]
            for c in vv: d[c] = pd.to_numeric(d[c], errors='coerce')   # DEN_CIBERBULLYING viene como string
            piezas.append(d.melt(id_vars='rbd', value_vars=vv, var_name='v', value_name='conteo'))
        e = pd.concat(piezas, ignore_index=True).dropna(subset=['conteo'])
        e = e[e.rbd.isin(validos)]
        e['tipo_evento_cod'] = e.v.map(MAPE); e['ventana_id'] = ven[etq]
        e['conteo'] = e.conteo.round().astype(int).clip(lower=0)
        e = e.drop_duplicates(['rbd','ventana_id','tipo_evento_cod'])
        ins(cx, 'hechos.sie_evento_agregado', e, ['rbd','ventana_id','tipo_evento_cod','conteo'])

    # ---------- core: conjunto de entrenamiento depurado ----------
    v11 = pd.read_parquet(B+'_historico/tabla_modelo_final_v11.parquet')
    rc = [c for c in v11.columns if c.lower()=='rbd'][0]
    ce = pd.DataFrame({'rbd': v11[rc].astype(int).unique()})
    ce = ce[ce.rbd.isin(validos)]
    ins(cx, 'core.conjunto_entrenamiento', ce, ['rbd'])

    # ---------- ml ----------
    mm = json.load(open(MB+'metadatos_modelos.json')); mg = json.load(open(MB+'metadatos_modelo_global.json'))
    med = json.load(open(MB+'medianas_imputacion.json'))
    def reg_modelo(nombre, alcance, factor, algo, ruta, nobs, ngrp, metricas, hp, feats):
        mid = cx.execute(text("""INSERT INTO ml.modelo (nombre,alcance,factor_cod,algoritmo_cod,version,ruta_artefacto,
                                 n_observaciones,n_grupos,en_produccion)
                                 VALUES (:n,:a,:f,:g,'1.0',:r,:o,:gr,TRUE)
                                 ON CONFLICT (nombre,version) DO NOTHING RETURNING modelo_id"""),
                        dict(n=nombre,a=alcance,f=factor,g=algo,r=ruta,o=nobs,gr=ngrp)).scalar()
        if mid is None: return
        tot['ml.modelo'] = tot.get('ml.modelo',0)+1
        for k, v in metricas.items():
            if v is None: continue
            cx.execute(text("INSERT INTO ml.modelo_metrica VALUES (:m,:c,:v) ON CONFLICT DO NOTHING"),
                       dict(m=mid,c=k,v=float(v))); tot['ml.modelo_metrica']=tot.get('ml.modelo_metrica',0)+1
        for k, v in (hp or {}).items():
            cx.execute(text("INSERT INTO ml.modelo_hiperparametro VALUES (:m,:n,:v) ON CONFLICT DO NOTHING"),
                       dict(m=mid,n=k,v=str(v))); tot['ml.modelo_hiperparametro']=tot.get('ml.modelo_hiperparametro',0)+1
        for o, ft in enumerate(feats or [], 1):
            cx.execute(text("""INSERT INTO ml.modelo_feature (modelo_id,feature,orden,mediana_imputacion)
                               VALUES (:m,:f,:o,:md) ON CONFLICT DO NOTHING"""),
                       dict(m=mid,f=ft,o=o,md=med.get(ft))); tot['ml.modelo_feature']=tot.get('ml.modelo_feature',0)+1

    for cod, d in mm.items():
        if cod.startswith('_'): continue
        reg_modelo(f'modelo_{cod}', 'FACTOR', cod, 'RF', f'models/registry/modelo_{cod}.joblib',
                   d.get('n_observaciones'), d.get('n_establecimientos'),
                   {'R2': d.get('r2'), 'MAE': d.get('mae')}, d.get('best_params'), d.get('features'))
    reg_modelo('modelo_global_INDICER', 'GLOBAL', None, 'HGB', f"models/registry/{mg['archivo']}",
               mg.get('n_observaciones'), mg.get('n_establecimientos'),
               {k.upper(): v for k, v in mg['metricas'].items()}, mg.get('hiperparametros'), mg.get('features_entrada'))

    cx.execute(text("REFRESH MATERIALIZED VIEW ml.mv_matriz_entrenamiento"))

print(f"{'tabla':<34}{'filas':>10}")
for k in sorted(tot): print(f"{k:<34}{tot[k]:>10,}")
