import { useEffect, useMemo, useRef, useState } from 'react'
import { evaluarEscenario, listarEstablecimientos, obtenerObservacion, obtenerPrediccion, obtenerRanking } from '../api'
import type { Observacion, Ranking } from '../tipos'

/* Metadatos de presentacion. El rango final lo valida el dominio: si un valor
   sale del admisible, el constructor de escenarios lo recorta en el servidor.
   `escala` traduce la unidad de la fuente (proporcion) a la que lee el usuario. */
type Palanca = {
  variable: string
  rotulo: string
  min: number
  max: number
  paso: number
  unidad?: string
  escala?: number
  negativa?: boolean
}

const PALANCAS: Palanca[] = [
  { variable: 'simce_lect_4b', rotulo: 'Lectura 4 basico', min: 150, max: 350, paso: 1, unidad: ' pts' },
  { variable: 'simce_mate_4b', rotulo: 'Matematica 4 basico', min: 150, max: 350, paso: 1, unidad: ' pts' },
  { variable: 'simce_lect_2m', rotulo: 'Lectura 2 medio', min: 150, max: 350, paso: 1, unidad: ' pts' },
  { variable: 'simce_mate_2m', rotulo: 'Matematica 2 medio', min: 150, max: 350, paso: 1, unidad: ' pts' },
  { variable: 'idps_cc_4b', rotulo: 'Clima de convivencia escolar', min: 0, max: 100, paso: 1 },
  { variable: 'idps_pf_4b', rotulo: 'Participacion y formacion ciudadana', min: 0, max: 100, paso: 1 },
  { variable: 'tasa_aprobacion', rotulo: 'Tasa de aprobacion', min: 60, max: 100, paso: 0.5, unidad: '%', escala: 100 },
  { variable: 'tasa_retiro', rotulo: 'Tasa de retiro', min: 0, max: 20, paso: 0.1, unidad: '%', escala: 100, negativa: true },
  { variable: 'n_docentes', rotulo: 'Dotacion docente', min: 5, max: 120, paso: 1 },
  { variable: 'procesos_con_sancion', rotulo: 'Procesos con sancion', min: 0, max: 20, paso: 1, negativa: true },
]

/* Variables de contexto: se muestran, no se mueven. */
const CONTEXTO: { variable: string; rotulo: string; escala?: number; unidad?: string }[] = [
  { variable: 'ive_consolidado', rotulo: 'IVE consolidado', escala: 100, unidad: '%' },
  { variable: 'matricula_total', rotulo: 'Matricula total' },
  { variable: 'n_vulnerables', rotulo: 'Alumnos prioritarios' },
  { variable: 'n_beneficiarios_sep', rotulo: 'Beneficiarios SEP' },
  { variable: 'n_asistentes', rotulo: 'Asistentes de la educacion' },
  { variable: 'n_directivos', rotulo: 'Cargos directivos' },
]

const CIRC = 2 * Math.PI * 96

function leer(obs: Observacion, clave: string): number | null {
  const v = obs[clave]
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

function fmt(n: number, decimales = 1): string {
  return n.toLocaleString('es-CL', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}

export default function Simulador({ rbd }: { rbd: string }) {
  const [observacion, setObservacion] = useState<Observacion | null>(null)
  const [indiceActual, setIndiceActual] = useState<number | null>(null)
  const [valores, setValores] = useState<Record<string, number>>({})
  const [proyectado, setProyectado] = useState<number | null>(null)
  const [incertidumbre, setIncertidumbre] = useState<number | null>(null)
  /* Indice OFICIAL publicado por el organismo, con el ciclo al que corresponde.
     Se muestra junto a la estimacion porque son cosas distintas y la pantalla
     debe permitir distinguirlas: uno es un hecho, el otro es un calculo. */
  const [oficial, setOficial] = useState<{ valor: number | null; ciclo: string | null }>({
    valor: null,
    ciclo: null,
  })
  const [ranking, setRanking] = useState<Ranking | null>(null)
  const [calculando, setCalculando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const temporizador = useRef<number | undefined>(undefined)

  /* Carga inicial: valores observados e indice de la situacion real. */
  useEffect(() => {
    let vigente = true
    setObservacion(null); setProyectado(null); setError(null)
    Promise.all([
      obtenerObservacion(rbd),
      obtenerPrediccion(rbd),
      listarEstablecimientos().catch(() => null),
      obtenerRanking(rbd).catch(() => null),
    ])
      .then(([obs, pred, listado, posicion]) => {
        if (!vigente) return
        const resumen = listado?.detalle.find((d) => String(d.rbd) === String(rbd))
        setOficial({ valor: resumen?.indicer ?? null, ciclo: resumen?.bienio_premio ?? null })
        setRanking(posicion)
        setObservacion(obs)
        setIndiceActual(pred.indice)
        setProyectado(pred.indice)
        setIncertidumbre(pred.incertidumbre_mae ?? null)
        const iniciales: Record<string, number> = {}
        PALANCAS.forEach((p) => {
          const v = leer(obs, p.variable)
          if (v !== null) iniciales[p.variable] = v * (p.escala ?? 1)
        })
        setValores(iniciales)
      })
      .catch((e) => { if (vigente) setError((e as Error).message) })
    return () => { vigente = false }
  }, [rbd])

  const disponibles = useMemo(
    () => PALANCAS.filter((p) => observacion !== null && valores[p.variable] !== undefined),
    [observacion, valores],
  )

  /* El escenario se evalua en el servidor, con debounce: el navegador no estima. */
  function programarEvaluacion(siguientes: Record<string, number>) {
    window.clearTimeout(temporizador.current)
    temporizador.current = window.setTimeout(async () => {
      setCalculando(true)
      try {
        const envio: Record<string, number> = {}
        PALANCAS.forEach((p) => {
          const v = siguientes[p.variable]
          if (v !== undefined) envio[p.variable] = v / (p.escala ?? 1)
        })
        const resp = await evaluarEscenario(rbd, envio)
        setProyectado(resp.indice)
        if (resp.incertidumbre_mae !== undefined) setIncertidumbre(resp.incertidumbre_mae ?? null)
        setError(null)
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setCalculando(false)
      }
    }, 400)
  }

  function mover(variable: string, valor: number) {
    const siguientes = { ...valores, [variable]: valor }
    setValores(siguientes)
    programarEvaluacion(siguientes)
  }

  function restablecer() {
    if (!observacion) return
    const iniciales: Record<string, number> = {}
    PALANCAS.forEach((p) => {
      const v = leer(observacion, p.variable)
      if (v !== null) iniciales[p.variable] = v * (p.escala ?? 1)
    })
    setValores(iniciales)
    setProyectado(indiceActual)
    window.clearTimeout(temporizador.current)
  }

  if (error && !observacion) return <div className="error">{error}</div>
  if (!observacion) return <div className="panel"><div className="cargando">Cargando las variables del establecimiento...</div></div>

  const indice = proyectado ?? indiceActual ?? 0
  const delta = indiceActual !== null ? indice - indiceActual : 0
  /* Banda de lectura del escenario: el valor central mas y menos el error medio
     del motor. No es un intervalo de confianza, y por eso se rotula como rango
     de lectura y no como minimo y maximo posibles: el indice real puede caer
     fuera. Pintar solo el numero central invita a leerlo como exacto. */
  const banda: [number, number] | null =
    incertidumbre !== null && Number.isFinite(incertidumbre) && incertidumbre > 0
      ? [Math.max(0, indice - incertidumbre), Math.min(100, indice + incertidumbre)]
      : null
  const color = indice >= 70 ? 'var(--verde)' : indice >= 55 ? 'var(--navy)' : 'var(--rojo)'

  return (
    <>
      <div className="cab">
        <div>
          <h2>Simulador SNED</h2>
          <p>Ajuste las variables de gestion y observe el efecto estimado sobre el indice del establecimiento.</p>
        </div>
      </div>

      <div className="rejilla-sim">
        <div className="panel">
          <div className="panel-cab">
            <h3>Variables de simulacion</h3>
            <div className="sub">RBD {rbd} · los valores iniciales son los observados en la fuente</div>
          </div>
          <div className="panel-cuerpo">
            <div className="grupo-var">
              <div className="grupo-tit">Variables que usted puede gestionar</div>
              {disponibles.map((p) => {
                const v = valores[p.variable]
                return (
                  <div className="var" key={p.variable}>
                    <div className="var-cab">
                      <span className="var-nom">{p.rotulo}</span>
                      <span className={`var-val ${p.negativa ? 'neg' : ''}`}>
                        {fmt(v, p.paso < 1 ? 1 : 0)}{p.unidad ?? ''}
                      </span>
                    </div>
                    <input
                      type="range"
                      className={p.negativa ? 'neg' : ''}
                      min={p.min} max={p.max} step={p.paso} value={v}
                      onChange={(e) => mover(p.variable, Number(e.target.value))}
                    />
                    <div className="var-lim">
                      <span>{p.min}{p.unidad ?? ''}</span>
                      <span>{p.max}{p.unidad ?? ''}</span>
                    </div>
                  </div>
                )
              })}
              {disponibles.length === 0 && (
                <div className="nota">La fuente no entrega ninguna de las variables simulables para este establecimiento.</div>
              )}
            </div>

            <div className="grupo-var" style={{ marginBottom: 16 }}>
              <div className="grupo-tit">Contexto del establecimiento — no modificable</div>
              <div className="fijas">
                {CONTEXTO.map((c) => {
                  const v = leer(observacion, c.variable)
                  return (
                    <div className="fija" key={c.variable}>
                      <div className="r">{c.rotulo}</div>
                      <div className="v">
                        {v === null ? 'Sin dato' : `${fmt(v * (c.escala ?? 1), c.escala ? 1 : 0)}${c.unidad ?? ''}`}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="secundario" onClick={restablecer}>Restablecer valores reales</button>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-cab">
            <h3>Indice SNED estimado</h3>
            <div className="sub">{calculando ? 'Consultando al motor...' : 'Resultado del escenario simulado'}</div>
          </div>
          <div className="panel-cuerpo">
            <div className="medidor">
              <div className="aro">
                <svg width="230" height="230" viewBox="0 0 230 230">
                  <circle cx="115" cy="115" r="96" fill="none" stroke="#EFF1F4" strokeWidth="20" />
                  <circle
                    cx="115" cy="115" r="96" fill="none" stroke={color} strokeWidth="20" strokeLinecap="round"
                    strokeDasharray={CIRC}
                    strokeDashoffset={CIRC - (CIRC * Math.max(0, Math.min(100, indice))) / 100}
                    style={{ transition: 'stroke-dashoffset .4s ease, stroke .3s ease' }}
                  />
                </svg>
                <div className="aro-centro">
                  <div className="aro-num">{fmt(indice)}</div>
                  <div className="aro-rot">
                    {banda ? `entre ${fmt(banda[0])} y ${fmt(banda[1])}` : 'Puntos'}
                  </div>
                </div>
              </div>
            </div>

            <div className="comparacion">
              <div className="comp">
                <div className="r">{oficial.ciclo ? `SNED ${oficial.ciclo}` : 'Indice oficial'}</div>
                <div className="v">{oficial.valor !== null ? fmt(oficial.valor) : '—'}</div>
              </div>
              {banda && (
                <>
                  <div className="comp">
                    <div className="r">Minimo estimado</div>
                    <div className="v" style={{ color: 'var(--rojo)' }}>{fmt(banda[0])}</div>
                  </div>
                  <div className="comp">
                    <div className="r">Maximo estimado</div>
                    <div className="v" style={{ color: 'var(--navy)' }}>{fmt(banda[1])}</div>
                  </div>
                </>
              )}
              <div className="comp">
                <div className="r">Diferencia</div>
                <div className="v" style={{ color: Math.abs(delta) < 0.05 ? 'var(--tenue)' : delta > 0 ? 'var(--verde)' : 'var(--rojo)' }}>
                  {delta >= 0 ? '+' : ''}{fmt(delta)}
                </div>
              </div>
            </div>

            {ranking && (
              <>
                <div className="comparacion" style={{ marginTop: 12 }}>
                  <div className="comp">
                    <div className="r">Lugar en su grupo</div>
                    <div className="v">{ranking.posicion_en_grupo} de {ranking.n_grupo}</div>
                  </div>
                  <div className="comp">
                    <div className="r">Grupo homogeneo</div>
                    <div className="v">{ranking.cluster_codigo}</div>
                  </div>
                  <div className="comp">
                    <div className="r">Premiados</div>
                    <div className="v">{ranking.premiados_en_grupo}</div>
                  </div>
                  {ranking.corte_premiado !== null && (
                    <div className="comp">
                      <div className="r">Corte del ciclo</div>
                      <div className="v" style={{ color: 'var(--rojo)' }}>{fmt(ranking.corte_premiado)}</div>
                    </div>
                  )}
                </div>

                {ranking.lideres.length > 0 && (
                  <div className="comparacion" style={{ marginTop: 12 }}>
                    {ranking.lideres.map((l) => (
                      <div
                        key={l.rbd}
                        className="comp"
                        style={l.es_consultado ? { borderColor: 'var(--navy)' } : undefined}
                      >
                        <div className="r">{l.posicion}. {l.nombre.slice(0, 26)}</div>
                        <div className="v">{l.indicer !== null ? fmt(l.indicer) : '—'}</div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {error && <div className="error" style={{ marginTop: 16 }}>{error}</div>}

            {banda && (
              <div className="aviso">
                <b>El movimiento que ve es menor que el margen de error del modelo.</b> El
                escenario da {fmt(indice)} y el motor se equivoca en promedio{' '}
                {fmt(incertidumbre ?? 0)} puntos, de modo que este resultado se lee{' '}
                <b>entre {fmt(banda[0])} y {fmt(banda[1])}</b>.
                {Math.abs(delta) > 0 && Math.abs(delta) < (incertidumbre ?? 0) && (
                  <> La diferencia de {delta >= 0 ? '+' : ''}{fmt(delta)} puntos que produce este
                  escenario es <b>menor que ese margen</b>: indica direccion, no una ganancia
                  medible.</>
                )}
                <div style={{ marginTop: '.5rem' }}>
                  El minimo y el maximo son el rango de lectura, no un piso ni un techo
                  garantizados: cerca de la mitad de los establecimientos cae fuera de esa banda.
                </div>
              </div>
            )}

            <div className="aviso">
              <b>Por que mover mucho una variable mueve poco el indice.</b> El indice se construye
              por escalamiento relativo frente al resto del pais: la posicion del establecimiento
              depende tanto de lo que haga el como de lo que hagan los demas. Mejorar de forma
              sostenida en una medicion puede desplazar el indice apenas unas decimas si el
              conjunto tambien mejora.
            </div>

            <div className="aviso-neutro">
              El tramo se asigna por posicion dentro del grupo homogeneo, no por un puntaje fijo.
              Un aumento del indice no garantiza cambio de tramo.
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
