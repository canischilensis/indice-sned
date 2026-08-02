import { useEffect, useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { simular } from '../api'
import type { Simulacion } from '../tipos'

const PALANCAS = [
  { variable: 'simce_mate_4b', etiqueta: 'SIMCE Matematica 4to basico' },
  { variable: 'simce_lect_4b', etiqueta: 'SIMCE Lectura 4to basico' },
  { variable: 'tasa_aprobacion', etiqueta: 'Tasa de aprobacion' },
  { variable: 'idps_cc_4b', etiqueta: 'IDPS Clima de convivencia 4to basico' },
  { variable: 'n_docentes', etiqueta: 'Dotacion docente' },
]

export default function Simulador({ rbd }: { rbd: string }) {
  const [variable, setVariable] = useState(PALANCAS[0].variable)
  const [datos, setDatos] = useState<Simulacion | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDatos(null); setError(null)
    simular(rbd, variable).then(setDatos).catch((e) => setError((e as Error).message))
  }, [rbd, variable])

  const serie = datos ? datos.valores.map((v, i) => ({ valor: v, indice: datos.predicciones[i] })) : []

  return (
    <>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Simulacion de escenarios &mdash; curva ICE</h3>
        <p style={{ color: 'var(--tenue)', fontSize: 13 }}>
          Recorre el rango de una variable de gestion manteniendo fijas las restantes.
          Es la base matematica del control, no una extrapolacion visual.
        </p>
        <select value={variable} onChange={(e) => setVariable(e.target.value)}>
          {PALANCAS.map((p) => <option key={p.variable} value={p.variable}>{p.etiqueta}</option>)}
        </select>
      </div>

      {error && <div className="panel error">{error}</div>}
      {!datos && !error && <div className="panel cargando">Simulando...</div>}

      {datos && (
        <>
          <div className="panel">
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={serie}>
                <CartesianGrid stroke="#24323f" />
                <XAxis dataKey="valor" stroke="#9aacbd" label={{ value: datos.etiqueta, position: 'insideBottom', offset: -4, fill: '#9aacbd' }} />
                <YAxis stroke="#9aacbd" domain={['auto', 'auto']} label={{ value: 'Indice SNED', angle: -90, position: 'insideLeft', fill: '#9aacbd' }} />
                <Tooltip contentStyle={{ background: '#17222e', border: '1px solid #24323f' }} />
                <Line type="monotone" dataKey="indice" stroke="#4a9eda" strokeWidth={2} dot={false} />
                {datos.valor_actual !== null && datos.prediccion_actual !== null && (
                  <ReferenceDot x={datos.valor_actual} y={datos.prediccion_actual} r={5} fill="#3fa87a" stroke="none" />
                )}
              </LineChart>
            </ResponsiveContainer>
            <div className="rejilla" style={{ marginTop: 12 }}>
              <div className="metrica">
                <div className="rotulo">Posicion actual</div>
                <div className="valor" style={{ fontSize: 22 }}>{datos.prediccion_actual?.toFixed(2)}</div>
                <div style={{ color: 'var(--tenue)', fontSize: 12 }}>con {datos.etiqueta} = {datos.valor_actual}</div>
              </div>
              <div className="metrica">
                <div className="rotulo">Monotonicidad</div>
                <div className="valor" style={{ fontSize: 22 }}>{datos.monotona ? 'Verificada' : 'No monotona'}</div>
                <div style={{ color: 'var(--tenue)', fontSize: 12 }}>Mover el control hacia arriba nunca baja el indice</div>
              </div>
            </div>
          </div>
          <div className="aviso">{datos.advertencia_magnitud}</div>
        </>
      )}
    </>
  )
}
