import { useEffect, useRef, useState } from 'react'
import { consultarAsesor } from '../api'
import type { LlamadaDeHerramienta, RespuestaAsesor, Turno } from '../tipos'

/* Nombre tecnico de la herramienta -> como se nombra ante un directivo. El
   agente no inventa herramientas: este mapa refleja el catalogo explicito del
   cuanto 5, y una clave desconocida se muestra tal cual en vez de ocultarse. */
const HERRAMIENTAS: Record<string, { rotulo: string; ayuda: string }> = {
  diagnostico_de_establecimiento: {
    rotulo: 'Diagnostico del establecimiento',
    ayuda: 'Consulto la estimacion del indice, las alertas activas y la posicion en el Grupo Homogeneo.',
  },
  explicacion_por_factor: {
    rotulo: 'Explicacion por factor',
    ayuda: 'Consulto los valores de Shapley del factor para ver que variables lo sostienen.',
  },
  simulacion_de_escenario: {
    rotulo: 'Simulacion de escenario',
    ayuda: 'Pidio al motor una estimacion con las variables de gestion modificadas.',
  },
}

/* Preguntas de arranque. Cubren las tres herramientas del catalogo y una
   consulta que el agente debe rechazar, para que el uso de los guardarrailes
   sea observable y no una promesa del manual. */
const SUGERENCIAS = [
  'Dame el diagnostico general del establecimiento',
  'Por que se nos cae el factor de superacion',
  'Que pasa si la asistencia sube tres puntos',
  'Me garantizas que ganamos la subvencion si hago esto',
]

function fmtCosto(usd: number): string {
  if (usd <= 0) return 'sin costo (proveedor determinista)'
  return `US$ ${usd.toFixed(5)}`
}

function Traza({ llamadas }: { llamadas: LlamadaDeHerramienta[] }) {
  if (llamadas.length === 0) {
    return (
      <div className="traza">
        <div className="traza-tit">Sin consulta de datos</div>
        <div className="nota">
          El agente respondio sin llamar a ninguna herramienta. Cuando esto ocurre no hay
          cifras que citar, y ninguna afirmacion numerica sobrevive al guardarrail G-02.
        </div>
      </div>
    )
  }
  return (
    <div className="traza">
      <div className="traza-tit">Que consulto para responder</div>
      {llamadas.map((ll, i) => {
        const meta = HERRAMIENTAS[ll.herramienta]
        return (
          <div key={`${ll.herramienta}-${i}`} className={`paso ${ll.exito ? '' : 'falla'}`}>
            <div className="paso-cab">
              <span className="paso-n">{i + 1}</span>
              <span className="paso-nom">{meta?.rotulo ?? ll.herramienta}</span>
              <span className={`pill ${ll.exito ? 'verde' : 'rojo'}`}>
                <span className="punto" />
                {ll.exito ? 'con datos' : 'sin datos'}
              </span>
              <span className="paso-ms">{ll.milisegundos} ms</span>
            </div>
            <div className="paso-det">{ll.resumen}</div>
            {meta && <div className="paso-ayuda">{meta.ayuda}</div>}
          </div>
        )
      })}
    </div>
  )
}

function Guardarrailes({ r }: { r: RespuestaAsesor }) {
  if (r.guardarrailes_aplicados.length === 0 && !r.rechazada) return null
  return (
    <div className="guardas">
      <span className="guardas-rot">Guardarrailes</span>
      {r.guardarrailes_aplicados.map((g) => (
        <span key={g} className="pill oscuro"><span className="punto" />{g}</span>
      ))}
      {r.rechazada && <span className="pill rojo"><span className="punto" />respuesta bloqueada</span>}
    </div>
  )
}

function Respuesta({ turno }: { turno: Turno }) {
  const r = turno.respuesta

  return (
    <div className="turno">
      <div className="pregunta">
        <span className="quien">Usted</span>
        <p>{turno.pregunta}</p>
        <span className="ctx">RBD {turno.rbd}</span>
      </div>

      {!r && !turno.error && (
        <div className="respuesta"><div className="cargando">Consultando el servicio del indice...</div></div>
      )}

      {turno.error && <div className="error">{turno.error}</div>}

      {r && (
        <div className={`respuesta ${r.rechazada ? 'bloqueada' : ''}`}>
          <span className="quien">Asesor</span>
          <p className="texto">{r.texto}</p>

          {r.rechazada && r.motivo_rechazo && (
            <div className="aviso">
              <b>Respuesta retenida.</b> {r.motivo_rechazo} El agente prefiere no responder antes
              que afirmar algo que no puede fundar en una consulta al servicio.
            </div>
          )}

          <Traza llamadas={r.llamadas} />
          <Guardarrailes r={r} />

          <div className="medicion">
            <span>{r.tokens_entrada + r.tokens_salida} tokens</span>
            <span>{fmtCosto(r.costo_usd)}</span>
            <span>{r.llamadas.reduce((a, ll) => a + ll.milisegundos, 0)} ms en herramientas</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Asesor({ rbd }: { rbd: string }) {
  const [turnos, setTurnos] = useState<Turno[]>([])
  const [texto, setTexto] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const fondo = useRef<HTMLDivElement | null>(null)
  const siguiente = useRef(1)

  useEffect(() => {
    fondo.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turnos])

  async function preguntar(pregunta: string) {
    const limpia = pregunta.trim()
    if (!limpia || ocupado) return

    const id = siguiente.current++
    setTurnos((previos) => [...previos, { id, pregunta: limpia, rbd, respuesta: null, error: null }])
    setTexto('')
    setOcupado(true)

    try {
      const r = await consultarAsesor(rbd, limpia)
      setTurnos((previos) => previos.map((t) => (t.id === id ? { ...t, respuesta: r } : t)))
    } catch (e) {
      const mensaje = (e as Error).message
      setTurnos((previos) => previos.map((t) => (t.id === id ? { ...t, error: mensaje } : t)))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <>
      <div className="cab">
        <div>
          <h2>Asesor de gestion</h2>
          <p>
            Pregunte en lenguaje natural sobre el establecimiento seleccionado. El asesor consulta
            las mismas rutas que usan las otras ventanas y muestra cual uso para cada respuesta.
          </p>
        </div>
      </div>

      <div className="aviso-neutro" style={{ marginTop: 0, marginBottom: 20 }}>
        El asesor <b>no calcula el indice ni aplica ponderaciones</b>: traduce y prioriza lo que el
        motor predictivo entrega. Toda cifra que aparezca en su respuesta proviene de una consulta
        al servicio; si no puede fundarla, no la escribe.
      </div>

      <div className="panel">
        <div className="panel-cab">
          <h3>Conversacion sobre el RBD {rbd}</h3>
          <div className="sub">
            El historial no se guarda: al cambiar de establecimiento o cerrar sesion, se pierde.
            Las decisiones que se tomen a partir de estas respuestas deben quedar registradas
            donde corresponda.
          </div>
        </div>

        <div className="panel-cuerpo conversacion">
          {turnos.length === 0 && (
            <div className="arranque">
              <div className="arranque-tit">Para empezar</div>
              <div className="selector">
                {SUGERENCIAS.map((s) => (
                  <button key={s} className="chip" disabled={ocupado} onClick={() => preguntar(s)}>
                    {s}
                  </button>
                ))}
              </div>
              <div className="nota">
                La ultima es intencional: sirve para ver como el agente rechaza una promesa de
                resultado en vez de complacerla.
              </div>
            </div>
          )}

          {turnos.map((t) => <Respuesta key={t.id} turno={t} />)}
          <div ref={fondo} />
        </div>

        <div className="redaccion">
          <textarea
            value={texto}
            rows={2}
            placeholder={`Pregunte sobre el establecimiento RBD ${rbd}...`}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); preguntar(texto) }
            }}
          />
          <button className="primario" disabled={ocupado || texto.trim().length < 3} onClick={() => preguntar(texto)}>
            {ocupado ? 'Consultando...' : 'Preguntar'}
          </button>
        </div>
      </div>

      <div className="aviso-neutro">
        La IA asiste; la decision estrategica la toma el equipo directivo. El asesor no accede a
        establecimientos fuera de su jurisdiccion: reenvia su credencial de sesion, de modo que el
        control de acceso lo evalua el servicio del indice, no el agente.
      </div>
    </>
  )
}
