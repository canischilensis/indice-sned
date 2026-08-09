import { useState } from 'react'
import { iniciarSesion } from '../api'
import type { Sesion } from '../tipos'

export default function Login({ alEntrar }: { alEntrar: (s: Sesion) => void }) {
  const [usuario, setUsuario] = useState('sostenedor.demo')
  const [clave, setClave] = useState('demo')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      alEntrar(await iniciarSesion(usuario, clave))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="acceso">
      <div className="caja">
        <div className="marca" style={{ padding: 0, marginBottom: 20 }}>
          <div className="cuadro" style={{ background: 'var(--navy)' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 21h18M5 21V10l7-5 7 5v11M9 21v-6h6v6" />
            </svg>
          </div>
          <div>
            <h2 style={{ margin: 0 }}>Indice SNED</h2>
          </div>
        </div>

        <p className="intro">
          Acceso para sostenedores y equipos directivos. La consulta queda restringida a los
          establecimientos bajo su jurisdiccion.
        </p>

        <form onSubmit={enviar} style={{ display: 'grid', gap: 14 }}>
          <div>
            <label htmlFor="usuario">Usuario</label>
            <input id="usuario" value={usuario} onChange={(e) => setUsuario(e.target.value)} autoComplete="username" />
          </div>
          <div>
            <label htmlFor="clave">Clave</label>
            <input id="clave" type="password" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="current-password" />
          </div>
          <button className="primario" type="submit" disabled={enviando}>
            {enviando ? 'Verificando...' : 'Ingresar'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>

        <p className="pie">
          Perfiles de demostracion: <code>sostenedor.demo</code>, <code>directora.demo</code>,{' '}
          <code>auditor.demo</code>. Clave <code>demo</code>.
        </p>
      </div>
    </div>
  )
}
