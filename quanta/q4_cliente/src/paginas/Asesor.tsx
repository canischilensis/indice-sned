import { useEffect, useRef, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'
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
  consulta_de_doctrina: {
    rotulo: 'Documentacion del proyecto',
    ayuda: 'Leyo las decisiones registradas del sistema. No consulto datos del establecimiento.',
  },
}

/* Aviso de procedencia documental.
 *
 * Una cifra que calculo el motor durante esta consulta y una que estaba escrita
 * en un documento hace meses no valen lo mismo, y hasta ahora la pantalla las
 * presentaba con la misma autoridad. El guardarrail ya las separa por dentro; si
 * la separacion no llega aqui, la auditoria es mas fina y la lectura sigue igual
 * de ciega. */
function Procedencia({ documentos, cifras }: { documentos: string[]; cifras: number[] }) {
  if (documentos.length === 0) return null
  const nombre = (ruta: string) => ruta.split('/').pop() ?? ruta
  return (
    <div className="traza">
      <div className="traza-tit">De donde salen las cifras</div>
      <div className="nota">
        Parte de lo que se afirma arriba proviene de la <b>documentacion del proyecto</b>, no de
        una consulta al motor. Fue cierto cuando se escribio y puede haber cambiado desde
        entonces. Las cifras calculadas para este establecimiento en esta consulta se distinguen
        porque el agente no las atribuye a ningun documento.
      </div>
      <div className="paso">
        <div className="paso-cab">
          <span className="paso-nom">Documentos consultados</span>
          <span className="pill">
            <span className="punto" />
            {cifras.length === 1 ? '1 cifra documental' : `${cifras.length} cifras documentales`}
          </span>
        </div>
        <div className="paso-det">{documentos.map(nombre).join(' · ')}</div>
        <div className="paso-ayuda">
          El agente debe nombrar el documento en la misma frase que la cifra. Si no lo hace, el
          guardarrail G-02 retira la respuesta en vez de dejarla pasar como si fuera una medicion.
        </div>
      </div>
    </div>
  )
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
          <Procedencia
            documentos={r.documentos_consultados ?? []}
            cifras={r.cifras_documentales ?? []}
          />
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

/* La conversacion NO vive aqui: vive en App y llega por propiedad.
 *
 * Cuando el estado era local, cambiar de pestana desmontaba este componente y
 * borraba el dialogo. La pantalla declara que el historial se pierde al cambiar
 * de establecimiento o cerrar sesion; el codigo era mas estricto que lo
 * declarado y lo perdia tambien al mirar el tablero un segundo.
 *
 * La conversacion pertenece a la sesion y al establecimiento, no a la pestana.
 * Subirla a App hace que el texto de la pantalla sea verdad, y de paso una
 * respuesta que llegue mientras el usuario esta en otra ventana no se pierde:
 * el actualizador pertenece a App y sigue vivo aunque esta vista no lo este. */
export default function Asesor({
  rbd,
  turnos,
  fijarTurnos,
}: {
  rbd: string
  turnos: Turno[]
  fijarTurnos: Dispatch<SetStateAction<Turno[]>>
}) {
  const [texto, setTexto] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const fondo = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    fondo.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turnos])

  async function preguntar(pregunta: string) {
    const limpia = pregunta.trim()
    if (!limpia || ocupado) return

    // El identificador se deriva de la conversacion y no de un contador local.
    // Un contador en `useRef` volvia a 1 cada vez que la vista se remontaba, de
    // modo que los turnos viejos y los nuevos colisionaban en la clave de React.
    // `ocupado` impide dos preguntas a la vez, que es lo que hace segura esta
    // lectura del maximo.
    const id = turnos.reduce((mayor, t) => Math.max(mayor, t.id), 0) + 1
    fijarTurnos((previos) => [...previos, { id, pregunta: limpia, rbd, respuesta: null, error: null }])
    setTexto('')
    setOcupado(true)

    try {
      const r = await consultarAsesor(rbd, limpia)
      fijarTurnos((previos) => previos.map((t) => (t.id === id ? { ...t, respuesta: r } : t)))
    } catch (e) {
      const mensaje = (e as Error).message
      fijarTurnos((previos) => previos.map((t) => (t.id === id ? { ...t, error: mensaje } : t)))
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
