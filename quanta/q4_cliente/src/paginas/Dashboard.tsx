import { useEffect, useState } from 'react'
import {
  listarEstablecimientos,
  obtenerAlertas,
  obtenerComposicion,
  obtenerObservacion,
  obtenerPrediccion,
} from '../api'
import type { Alerta, Composicion, FilaTablero } from '../tipos'

/** Margen bajo el cual se considera que el establecimiento arriesga su tramo. */
const MARGEN_RIESGO = 1.5

function num(valor: unknown): number | null {
  return typeof valor === 'number' && Number.isFinite(valor) ? valor : null
}

function cifra(n: number | null, decimales = 1): string {
  return n === null ? '—' : n.toLocaleString('es-CL', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}

export default function Dashboard({ rbds }: { rbds: string[] }) {
  const [filas, setFilas] = useState<FilaTablero[] | null>(null)
  const [composicion, setComposicion] = useState<Composicion | null>(null)
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let vigente = true
    setFilas(null); setError(null)

    async function cargar() {
      const listado = await listarEstablecimientos()
      const porRbd = new Map(listado.detalle.map((d) => [String(d.rbd), d]))

      const resultados = await Promise.all(
        rbds.map(async (rbd): Promise<FilaTablero> => {
          const resumen = porRbd.get(rbd)
          const base: FilaTablero = {
            rbd,
            nombre: `RBD ${rbd}`,
            matricula: null,
            cluster: resumen?.cluster_codigo ?? null,
            bienio: resumen?.bienio_premio ?? null,
            indicerOficial: resumen?.indicer ?? null,
            estimacion: null,
            error: null,
          }
          try {
            const [prediccion, observacion] = await Promise.all([
              obtenerPrediccion(rbd),
              obtenerObservacion(rbd).catch(() => ({}) as Record<string, unknown>),
            ])
            const nombre = observacion['nom_rbd'] ?? observacion['NOM_RBD']
            return {
              ...base,
              nombre: typeof nombre === 'string' && nombre ? nombre : base.nombre,
              matricula: num(observacion['matricula_total']),
              estimacion: prediccion.indice,
            }
          } catch (e) {
            return { ...base, error: (e as Error).message }
          }
        }),
      )
      if (!vigente) return
      setFilas(resultados)

      const composicionSalud = await obtenerComposicion().catch(() => null)
      if (vigente && composicionSalud) setComposicion(composicionSalud)

      const primero = resultados.find((f) => f.estimacion !== null)
      if (primero) {
        const resp = await obtenerAlertas(primero.rbd).catch(() => null)
        if (vigente && resp) setAlertas(resp.alertas)
      }
    }

    cargar().catch((e) => { if (vigente) setError((e as Error).message) })
    return () => { vigente = false }
  }, [rbds.join(',')])

  if (error) return <div className="error">{error}</div>
  if (!filas) return <div className="panel"><div className="cargando">Consolidando los establecimientos de la red...</div></div>

  const conEstimacion = filas.filter((f) => f.estimacion !== null)
  const matriculaTotal = filas.reduce((a, f) => a + (f.matricula ?? 0), 0)
  const indicePromedio = conEstimacion.length
    ? conEstimacion.reduce((a, f) => a + (f.estimacion ?? 0), 0) / conEstimacion.length
    : null
  const cobertura = composicion?.cobertura_de_variables ?? null
  const enRiesgo = filas.filter(
    (f) => f.estimacion !== null && f.indicerOficial !== null && f.estimacion - f.indicerOficial < -MARGEN_RIESGO,
  ).length

  return (
    <>
      <div className="cab">
        <div>
          <h2>Tablero Sostenedor</h2>
          <p>Resumen consolidado de los establecimientos bajo su jurisdiccion.</p>
        </div>
      </div>

      <div className="rejilla-kpi">
        <div className="metrica">
          <div className="metrica-cab"><span className="rotulo">Total de estudiantes</span></div>
          <div className="valor">{matriculaTotal ? Math.round(matriculaTotal).toLocaleString('es-CL') : '—'}</div>
          <div className="nota">Matricula sumada de {filas.length} establecimiento{filas.length === 1 ? '' : 's'}</div>
        </div>

        <div className="metrica">
          <div className="metrica-cab"><span className="rotulo">Indice SNED promedio</span></div>
          <div className="valor">{cifra(indicePromedio)}</div>
          <div className="nota">Escala 0-100 · promedio de {conEstimacion.length} estimacion{conEstimacion.length === 1 ? '' : 'es'}</div>
        </div>

        <div className="metrica">
          <div className="metrica-cab"><span className="rotulo alerta">Alertas SNED</span></div>
          <div className={`valor ${enRiesgo > 0 ? 'alerta' : ''}`}>{enRiesgo}</div>
          <div className={`nota ${enRiesgo > 0 ? 'baja' : ''}`}>
            Establecimientos cuya estimacion cae mas de {MARGEN_RIESGO} puntos bajo su indice vigente
          </div>
        </div>

        <div className="metrica">
          <div className="metrica-cab"><span className="rotulo">Cobertura de datos</span></div>
          <div className="valor">
            {cobertura?.cobertura !== undefined ? `${(cobertura.cobertura * 100).toFixed(1)}%` : '—'}
          </div>
          <div className="nota">
            {cobertura === null
              ? 'Consultando la composicion del motor...'
              : cobertura.evaluable
                ? `${cobertura.n_disponibles} de ${cobertura.n_requeridas} variables disponibles en la fuente`
                : (cobertura.motivo ?? 'El repositorio no declara sus columnas.')}
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-cab">
          <h3>Estado de los establecimientos</h3>
          <div className="sub">
            El indice se calcula para el establecimiento completo, considerando todos sus niveles
            en conjunto: es el establecimiento el que obtiene el beneficio, no un curso.
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>RBD</th>
              <th>Establecimiento</th>
              <th>Matricula</th>
              <th>Grupo</th>
              <th>Indice vigente</th>
              <th>Estimacion del modelo</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => {
              const d = f.estimacion !== null && f.indicerOficial !== null ? f.estimacion - f.indicerOficial : null
              const riesgo = d !== null && d < -MARGEN_RIESGO
              const limite = d !== null && d < 0 && !riesgo
              return (
                <tr key={f.rbd}>
                  <td className="rbd">{f.rbd}</td>
                  <td className="nombre">{f.nombre}</td>
                  <td className="num">{f.matricula !== null ? Math.round(f.matricula).toLocaleString('es-CL') : '—'}</td>
                  <td className="num">{f.cluster ?? '—'}</td>
                  <td>
                    {f.indicerOficial !== null
                      ? <span className="pill oscuro"><span className="punto" />{cifra(f.indicerOficial)}{f.bienio ? ` · ${f.bienio}` : ''}</span>
                      : <span className="pill ambar"><span className="punto" />Sin ciclo previo</span>}
                  </td>
                  <td>
                    {f.error && <span className="pill rojo"><span className="punto" />{f.error}</span>}
                    {!f.error && (
                      <div className="estimacion">
                        <span className="num" style={{ fontWeight: 600 }}>{cifra(f.estimacion)}</span>
                        {d !== null && (
                          <span className={`delta ${riesgo || limite ? 'baja' : 'sube'}`}>
                            {d >= 0 ? '+' : ''}{cifra(d)}
                          </span>
                        )}
                        {riesgo && <span className="pill rojo"><span className="punto" />En riesgo</span>}
                        {limite && <span className="pill ambar"><span className="punto" />Al limite</span>}
                        {d !== null && d >= 0 && <span className="pill verde"><span className="punto" />Holgado</span>}
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {alertas.length > 0 && (
        <div className="panel">
          <div className="panel-cab">
            <h3>Alertas del establecimiento seleccionado</h3>
            <div className="sub">Tipologias que el motor detecta sobre la estimacion vigente.</div>
          </div>
          <div className="panel-cuerpo">
            {alertas.map((a) => (
              <div key={a.tipo} className={`alerta-item ${a.severidad === 'alta' ? 'alta' : ''}`}>
                <strong>{a.titulo}</strong>
                <div>{a.detalle}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="aviso-neutro">
        <b>Como leer la estimacion.</b> El modelo estima el indice del ciclo a partir de las
        variables observadas del establecimiento; no pronostica resultados futuros ni reemplaza
        el calculo oficial del organismo. Un establecimiento marcado en riesgo tiene una
        estimacion por debajo del indice que ostenta hoy.
      </div>
    </>
  )
}
