import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { obtenerAlertas, obtenerPrediccion } from '../api'
import type { Alerta, Prediccion } from '../tipos'

export default function Dashboard({ rbd }: { rbd: string }) {
  const [datos, setDatos] = useState<Prediccion | null>(null)
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDatos(null); setError(null)
    obtenerPrediccion(rbd).then(setDatos).catch((e) => setError((e as Error).message))
    obtenerAlertas(rbd).then((r) => setAlertas(r.alertas)).catch(() => setAlertas([]))
  }, [rbd])

  if (error) return <div className="panel error">{error}</div>
  if (!datos) return <div className="panel cargando">Calculando estimacion...</div>

  const serie = datos.factores.map((f) => ({
    nombre: f.nombre,
    aporte: f.aporte_al_indice,
    acotado: f.es_acotado,
  }))

  return (
    <>
      <div className="rejilla">
        <div className="metrica">
          <div className="rotulo">Indice SNED estimado</div>
          <div className="valor">{datos.indice.toFixed(2)}</div>
          <div style={{ color: 'var(--tenue)', fontSize: 12 }}>
            Escala 0-100 &middot; error medio &plusmn;{datos.incertidumbre_mae?.toFixed(2) ?? '—'} puntos
          </div>
        </div>
        <div className="metrica">
          <div className="rotulo">Motor</div>
          <div className="valor" style={{ fontSize: 20 }}>{datos.estrategia}</div>
          <div style={{ color: 'var(--tenue)', fontSize: 12 }}>version {datos.version_modelo}</div>
        </div>
        <div className="metrica">
          <div className="rotulo">Factores acotados</div>
          <div className="valor" style={{ fontSize: 20 }}>
            {datos.factores.filter((f) => f.es_acotado).length} de {datos.factores.length}
          </div>
          <div className="acotado">Limitados por informacion no publica</div>
        </div>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Aporte de cada factor al indice</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={serie} layout="vertical" margin={{ left: 60 }}>
            <XAxis type="number" stroke="#9aacbd" />
            <YAxis type="category" dataKey="nombre" stroke="#9aacbd" width={150} />
            <Tooltip contentStyle={{ background: '#17222e', border: '1px solid #24323f' }} />
            <Bar dataKey="aporte" radius={[0, 4, 4, 0]}>
              {serie.map((s, i) => (
                <Cell key={i} fill={s.acotado ? '#d9a34f' : '#4a9eda'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <table>
          <thead>
            <tr><th>Factor</th><th>Peso</th><th>Valor</th><th>Aporte</th><th>Restriccion</th></tr>
          </thead>
          <tbody>
            {datos.factores.map((f) => (
              <tr key={f.codigo}>
                <td>{f.nombre}</td>
                <td>{(f.peso * 100).toFixed(0)} %</td>
                <td>{f.valor.toFixed(2)}</td>
                <td>{f.aporte_al_indice.toFixed(2)}</td>
                <td className="acotado">{f.restriccion ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Alertas tempranas</h3>
        {alertas.map((a) => (
          <div key={a.tipo} className={`alerta ${a.severidad === 'alta' ? 'alta' : ''}`}>
            <strong>{a.titulo}</strong>
            <div style={{ fontSize: 13, color: 'var(--tenue)', marginTop: 4 }}>{a.detalle}</div>
          </div>
        ))}
      </div>

      <div className="aviso">{datos.advertencia}</div>
    </>
  )
}
