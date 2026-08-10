import { useState } from 'react'
import Login from './componentes/Login'
import Dashboard from './paginas/Dashboard'
import Simulador from './paginas/Simulador'
import ReporteXAI from './paginas/ReporteXAI'
import Asesor from './paginas/Asesor'
import { cerrarSesion } from './api'
import type { Sesion } from './tipos'

type Ventana = 'tablero' | 'simulador' | 'xai' | 'asesor'

const VENTANAS: { id: Ventana; rotulo: string; icono: JSX.Element }[] = [
  {
    id: 'tablero',
    rotulo: 'Tablero Sostenedor',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    id: 'simulador',
    rotulo: 'Simulador SNED',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 20V10M12 20V4M20 20v-6" />
      </svg>
    ),
  },
  {
    id: 'xai',
    rotulo: 'Reporte XAI',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    id: 'asesor',
    rotulo: 'Asesor de gestion',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.9 8.9 0 0 1-3.8-.9L3 21l2-4.9A8.4 8.4 0 0 1 12 3a8.4 8.4 0 0 1 9 8.5z" />
      </svg>
    ),
  },
]

export default function App() {
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [ventana, setVentana] = useState<Ventana>('tablero')
  const [rbd, setRbd] = useState<string>('')

  if (!sesion) {
    return <Login alEntrar={(s) => { setSesion(s); setRbd(s.rbds[0] ?? '') }} />
  }

  const iniciales = sesion.rol.slice(0, 2).toUpperCase()

  return (
    <div className="app">
      <aside className="lateral">
        <div className="marca">
          <div className="cuadro">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0C1B33" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 21h18M5 21V10l7-5 7 5v11M9 21v-6h6v6" />
            </svg>
          </div>
          <div>
            <h1>Indice SNED</h1>
            <span>Gestion educacional</span>
          </div>
        </div>

        <nav className="nav">
          {VENTANAS.map((v) => (
            <button key={v.id} className={ventana === v.id ? 'on' : ''} onClick={() => setVentana(v.id)}>
              {v.icono}
              {v.rotulo}
            </button>
          ))}
        </nav>

        <div className="pie-lateral">
          La IA asiste; la decision estrategica la toma el equipo directivo.
        </div>
      </aside>

      <main className="principal">
        <header className="barra-sup">
          {sesion.rbds.length > 0 && (
            <select className="selector-rbd" value={rbd} onChange={(e) => setRbd(e.target.value)}>
              {sesion.rbds.map((r) => <option key={r} value={r}>Establecimiento RBD {r}</option>)}
            </select>
          )}
          <div className="acciones-sup">
            <span className="rol">{sesion.rol}</span>
            <div className="avatar">{iniciales}</div>
            <button className="secundario" onClick={() => { cerrarSesion(); setSesion(null) }}>Salir</button>
          </div>
        </header>

        <div className="contenido">
          {sesion.rbds.length === 0 && (
            <div className="panel">
              <div className="panel-cuerpo">
                Su perfil no tiene establecimientos asignados. El control de acceso limita la
                consulta a los establecimientos bajo su jurisdiccion.
              </div>
            </div>
          )}
          {rbd && ventana === 'tablero' && <Dashboard rbds={sesion.rbds} />}
          {rbd && ventana === 'simulador' && <Simulador rbd={rbd} />}
          {rbd && ventana === 'xai' && <ReporteXAI rbd={rbd} />}
          {rbd && ventana === 'asesor' && <Asesor key={rbd} rbd={rbd} />}
        </div>
      </main>
    </div>
  )
}
