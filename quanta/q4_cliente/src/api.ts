import type { Alerta, Explicacion, Prediccion, Sesion, Simulacion } from './tipos'

const BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

let sesion: Sesion | null = null

export function sesionActual(): Sesion | null {
  return sesion
}

async function pedir<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const cabeceras: Record<string, string> = { 'Content-Type': 'application/json' }
  if (sesion) cabeceras.Authorization = `Bearer ${sesion.token}`

  const respuesta = await fetch(`${BASE}${ruta}`, { ...init, headers: { ...cabeceras, ...(init.headers ?? {}) } })
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({ detail: respuesta.statusText }))
    throw new Error(cuerpo.detail ?? `Error ${respuesta.status}`)
  }
  return respuesta.json() as Promise<T>
}

export async function iniciarSesion(usuario: string, clave: string): Promise<Sesion> {
  const cuerpo = new URLSearchParams({ username: usuario, password: clave })
  const respuesta = await fetch(`${BASE}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: cuerpo,
  })
  if (!respuesta.ok) throw new Error('Credenciales invalidas')
  const datos = await respuesta.json()
  sesion = { token: datos.access_token, rol: datos.rol, rbds: datos.rbds }
  return sesion
}

export function cerrarSesion(): void {
  sesion = null
}

export const obtenerPrediccion = (rbd: string) => pedir<Prediccion>(`/prediccion/${rbd}`)
export const obtenerAlertas = (rbd: string) => pedir<{ rbd: string; alertas: Alerta[] }>(`/prediccion/${rbd}/alertas`)
export const obtenerShapley = (rbd: string, factor: string) =>
  pedir<Explicacion>(`/xai/${rbd}/shapley?factor=${factor}`)
export const simular = (rbd: string, variable: string, nPuntos = 25) =>
  pedir<Simulacion>('/xai/simular', {
    method: 'POST',
    body: JSON.stringify({ rbd, variable, n_puntos: nPuntos, variables: {} }),
  })
