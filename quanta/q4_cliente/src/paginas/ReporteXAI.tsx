import { useEffect, useState } from 'react'
import { obtenerPrediccion, obtenerShapley } from '../api'
import type { Contribucion, Explicacion, FactorPredicho } from '../tipos'

function fmt(n: number, decimales = 2): string {
  return n.toLocaleString('es-CL', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}

function Barra({ c, maximo }: { c: Contribucion; maximo: number }) {
  const positiva = c.contribucion >= 0
  const ancho = Math.min(50, (Math.abs(c.contribucion) / maximo) * 50)
  return (
    <div className="fila-b">
      <div className="et">
        {c.etiqueta}
        <small>{c.valor === null ? 'sin medicion' : `valor observado: ${fmt(c.valor, 2)}`}</small>
      </div>
      <div className="pista">
        <div className="mitad" />
        <div className={`barra ${positiva ? 'pos' : 'neg'}`} style={{ width: `${ancho}%` }} />
      </div>
      <div className={`cifra ${positiva ? 'pos' : 'neg'}`}>
        {positiva ? '+' : ''}{fmt(c.contribucion)}
      </div>
    </div>
  )
}

export default function ReporteXAI({ rbd }: { rbd: string }) {
  const [factores, setFactores] = useState<FactorPredicho[]>([])
  const [factor, setFactor] = useState<string>('')
  const [datos, setDatos] = useState<Explicacion | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let vigente = true
    setFactores([]); setDatos(null); setError(null)
    obtenerPrediccion(rbd)
      .then((p) => {
        if (!vigente) return
        setFactores(p.factores)
        setFactor(p.factores[0]?.codigo ?? '')
      })
      .catch((e) => { if (vigente) setError((e as Error).message) })
    return () => { vigente = false }
  }, [rbd])

  useEffect(() => {
    if (!factor) return
    let vigente = true
    setDatos(null); setError(null)
    obtenerShapley(rbd, factor)
      .then((d) => { if (vigente) setDatos(d) })
      .catch((e) => { if (vigente) setError((e as Error).message) })
    return () => { vigente = false }
  }, [rbd, factor])

  const actual = factores.find((f) => f.codigo === factor)
  const positivas = (datos?.contribuciones ?? []).filter((c) => c.contribucion >= 0)
  const negativas = (datos?.contribuciones ?? []).filter((c) => c.contribucion < 0)
  const maximo = Math.max(1e-6, ...(datos?.contribuciones ?? []).map((c) => Math.abs(c.contribucion)))
  const diferencia = datos ? datos.prediccion - datos.valor_base : 0

  return (
    <>
      <div className="cab">
        <div>
          <h2>Reporte de explicabilidad</h2>
          <p>Que variables sostienen la estimacion de cada factor, y con cuanto peso.</p>
        </div>
      </div>

      <div className="selector">
        {factores.map((f) => (
          <button
            key={f.codigo}
            className={`chip ${f.codigo === factor ? 'on' : ''}`}
            onClick={() => setFactor(f.codigo)}
          >
            {f.es_acotado && <span className="ac" />}
            {f.nombre}
            <span className="peso">{(f.peso * 100).toFixed(0)}%</span>
          </button>
        ))}
      </div>

      {error && <div className="error">{error}</div>}
      {!error && !datos && <div className="panel"><div className="cargando">Calculando valores de Shapley...</div></div>}

      {datos && (
        <>
          <div className="rejilla-3">
            <div className="metrica">
              <div className="metrica-cab"><span className="rotulo">Punto de partida</span></div>
              <div className="valor">{fmt(datos.valor_base)}</div>
              <div className="nota">Promedio del factor en el conjunto nacional</div>
            </div>
            <div className="metrica">
              <div className="metrica-cab"><span className="rotulo">Estimacion del factor</span></div>
              <div className="valor">{fmt(datos.prediccion)}</div>
              <div className={`nota ${diferencia >= 0 ? 'sube' : 'baja'}`}>
                {diferencia >= 0 ? '+' : ''}{fmt(diferencia)} respecto del promedio
              </div>
            </div>
            <div className="metrica">
              <div className="metrica-cab"><span className="rotulo">Explicacion verificada</span></div>
              <div className="valor" style={{ fontSize: 25, color: datos.aditividad_verificada ? 'var(--verde)' : 'var(--rojo)' }}>
                {datos.aditividad_verificada ? 'Si' : 'Revisar'}
              </div>
              <div className="nota">
                {datos.aditividad_verificada
                  ? 'Las contribuciones suman exactamente la diferencia'
                  : 'La suma de contribuciones no reproduce la prediccion'}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-cab">
              <h3>Que empuja el resultado hacia arriba y hacia abajo</h3>
              <div className="sub">
                Cada barra es cuanto aporta esa variable respecto del promedio nacional, ordenadas
                por magnitud. Una variable sin medicion se declara como tal, no se trata como cero.
              </div>
            </div>
            <div className="panel-cuerpo">
              {positivas.length > 0
                ? positivas.map((c) => <Barra key={c.variable} c={c} maximo={maximo} />)
                : <div className="nota">Ninguna variable empuja este factor por encima del promedio.</div>}

              <div className="separador">Promedio nacional del factor</div>

              {negativas.length > 0
                ? negativas.map((c) => <Barra key={c.variable} c={c} maximo={maximo} />)
                : <div className="nota">Ninguna variable empuja este factor por debajo del promedio.</div>}

              <div className="lectura">
                <div className="tit">Como leerlo</div>
                <p>{datos.lectura}</p>
                {actual?.es_acotado && (
                  <p style={{ marginTop: 10 }}>
                    <b style={{ color: 'var(--ambar)' }}>Factor acotado.</b>{' '}
                    {actual.restriccion ?? 'Parte de la informacion que el organismo usa para calcularlo no es publica.'}{' '}
                    Esta estimacion tiene menos respaldo que la de los factores sin restriccion.
                  </p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
