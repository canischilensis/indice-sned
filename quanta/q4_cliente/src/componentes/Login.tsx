import { useState } from 'react'
import { iniciarSesion } from '../api'
import type { Sesion } from '../tipos'

export default function Login({ alEntrar }: { alEntrar: (s: Sesion) => void }) {
  const [usuario, setUsuario] = useState('directora.demo')
  const [clave, setClave] = useState('demo')
  const [error, setError] = useState<string | null>(null)

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      alEntrar(await iniciarSesion(usuario, clave))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="contenedor" style={{ maxWidth: 420, paddingTop: 80 }}>
      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Simulador Indice SNED</h2>
        <p style={{ color: 'var(--tenue)', fontSize: 13 }}>
          Acceso B2B para sostenedores y equipos directivos. El acceso queda restringido
          a los establecimientos bajo su jurisdiccion (RBAC).
        </p>
        <form onSubmit={enviar} style={{ display: 'grid', gap: 12 }}>
          <input value={usuario} onChange={(e) => setUsuario(e.target.value)} placeholder="Usuario" />
          <input type="password" value={clave} onChange={(e) => setClave(e.target.value)} placeholder="Clave" />
          <button className="primario" type="submit">Ingresar</button>
          {error && <div className="error">{error}</div>}
        </form>
        <p style={{ color: 'var(--tenue)', fontSize: 12, marginBottom: 0 }}>
          Demo: <code>directora.demo</code> / <code>sostenedor.demo</code> / <code>auditor.demo</code>, clave <code>demo</code>
        </p>
      </div>
    </div>
  )
}
