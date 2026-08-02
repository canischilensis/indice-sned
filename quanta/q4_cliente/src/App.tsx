import { useState } from 'react'
import Login from './componentes/Login'
import Dashboard from './paginas/Dashboard'
import Simulador from './paginas/Simulador'
import ReporteXAI from './paginas/ReporteXAI'
import { cerrarSesion } from './api'
import type { Sesion } from './tipos'

type Ventana = 'dashboard' | 'simulador' | 'xai'

export default function App() {
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [ventana, setVentana] = useState<Ventana>('dashboard')
  const [rbd, setRbd] = useState<string>('')

  if (!sesion) {
    return <Login alEntrar={(s) => { setSesion(s); setRbd(s.rbds[0] ?? '') }} />
  }

  return (
    <>
      <header className="barra">
        <h1>Simulador Indice SNED</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select value={rbd} onChange={(e) => setRbd(e.target.value)}>
            {sesion.rbds.map((r) => <option key={r} value={r}>RBD {r}</option>)}
          </select>
          <span style={{ color: 'var(--tenue)', fontSize: 13 }}>{sesion.rol}</span>
          <button onClick={() => { cerrarSesion(); setSesion(null) }}>Salir</button>
        </div>
      </header>

      <div className="contenedor">
        <nav className="pestanas">
          <button className={ventana === 'dashboard' ? 'activa' : ''} onClick={() => setVentana('dashboard')}>
            1. Dashboard
          </button>
          <button className={ventana === 'simulador' ? 'activa' : ''} onClick={() => setVentana('simulador')}>
            2. Simulador
          </button>
          <button className={ventana === 'xai' ? 'activa' : ''} onClick={() => setVentana('xai')}>
            3. Reporte XAI
          </button>
        </nav>

        {!rbd && <div className="panel">Su perfil no tiene establecimientos asignados.</div>}
        {rbd && ventana === 'dashboard' && <Dashboard rbd={rbd} />}
        {rbd && ventana === 'simulador' && <Simulador rbd={rbd} />}
        {rbd && ventana === 'xai' && <ReporteXAI rbd={rbd} />}
      </div>
    </>
  )
}
