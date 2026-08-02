import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { obtenerShapley } from '../api'
import type { Explicacion } from '../tipos'

const FACTORES = [
  { codigo: 'EFECTIVR', nombre: 'Efectividad (37 %)' },
  { codigo: 'SUPERAR', nombre: 'Superacion (28 %)' },
  { codigo: 'IGUALDR', nombre: 'Igualdad (22 %)' },
  { codigo: 'INICIAR', nombre: 'Iniciativa (6 %)' },
  { codigo: 'INTEGRAR', nombre: 'Integracion (5 %)' },
  { codigo: 'MEJORAR', nombre: 'Mejoramiento (2 %)' },
]

export default function ReporteXAI({ rbd }: { rbd: string }) {
  const [factor, setFactor] = useState('EFECTIVR')
  const [datos, setDatos] = useState<Explicacion | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDatos(null); setError(null)
    obtenerShapley(rbd, factor).then(setDatos).catch((e) => setError((e as Error).message))
  }, [rbd, factor])

  const serie = datos
    ? datos.contribuciones.slice(0, 12).map((c) => ({ etiqueta: c.etiqueta, contribucion: c.contribucion }))
    : []

  return (
    <>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Reporte de explicabilidad &mdash; valores de Shapley</h3>
        <p style={{ color: 'var(--tenue)', fontSize: 13 }}>
          Descompone la estimacion de este establecimiento en la contribucion individual de cada
          variable, con signo y magnitud. Las contribuciones suman exactamente la diferencia entre
          la prediccion y el valor base.
        </p>
        <select value={factor} onChange={(e) => setFactor(e.target.value)}>
          {FACTORES.map((f) => <option key={f.codigo} value={f.codigo}>{f.nombre}</option>)}
        </select>
      </div>

      {error && <div className="panel error">{error}</div>}
      {!datos && !error && <div className="panel cargando">Calculando valores de Shapley...</div>}

      {datos && (
        <>
          <div className="rejilla">
            <div className="metrica">
              <div className="rotulo">Valor base</div>
              <div className="valor" style={{ fontSize: 24 }}>{datos.valor_base.toFixed(2)}</div>
              <div style={{ color: 'var(--tenue)', fontSize: 12 }}>promedio del conjunto</div>
            </div>
            <div className="metrica">
              <div className="rotulo">Estimacion del factor</div>
              <div className="valor" style={{ fontSize: 24 }}>{datos.prediccion.toFixed(2)}</div>
              <div style={{ color: 'var(--tenue)', fontSize: 12 }}>
                {(datos.prediccion - datos.valor_base >= 0 ? '+' : '')}
                {(datos.prediccion - datos.valor_base).toFixed(2)} respecto del promedio
              </div>
            </div>
            <div className="metrica">
              <div className="rotulo">Aditividad</div>
              <div className="valor" style={{ fontSize: 24 }}>{datos.aditividad_verificada ? 'OK' : 'Revisar'}</div>
              <div style={{ color: 'var(--tenue)', fontSize: 12 }}>base + contribuciones = prediccion</div>
            </div>
          </div>

          <div className="panel">
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={serie} layout="vertical" margin={{ left: 140 }}>
                <XAxis type="number" stroke="#9aacbd" />
                <YAxis type="category" dataKey="etiqueta" stroke="#9aacbd" width={230} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#17222e', border: '1px solid #24323f' }} />
                <Bar dataKey="contribucion" radius={[0, 4, 4, 0]}>
                  {serie.map((s, i) => (
                    <Cell key={i} fill={s.contribucion >= 0 ? '#3fa87a' : '#d97a7a'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="aviso"><strong>Lectura:</strong> {datos.lectura}</div>
        </>
      )}
    </>
  )
}
