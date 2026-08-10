import type {
  Alerta,
  Composicion,
  Explicacion,
  Observacion,
  Prediccion,
  Ranking,
  RespuestaAsesor,
  RespuestaEstablecimientos,
  Sesion,
  Simulacion,
} from './tipos'

const BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

/** El asesor es otro proceso, en otro puerto. La direccion es deliberadamente
 *  distinta de BASE: son dos unidades de despliegue, no dos rutas del mismo
 *  servicio. */
const BASE_ASESOR = import.meta.env.VITE_AGENTE_URL ?? 'http://127.0.0.1:8010'

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

/* -------------------------------------------------------------------------
 * Lecturas. El cliente no calcula: solo pide y muestra.
 * ---------------------------------------------------------------------- */

export const obtenerPrediccion = (rbd: string) => pedir<Prediccion>(`/prediccion/${rbd}`)

export const obtenerAlertas = (rbd: string) =>
  pedir<{ rbd: string; alertas: Alerta[] }>(`/prediccion/${rbd}/alertas`)

export const obtenerShapley = (rbd: string, factor: string) =>
  pedir<Explicacion>(`/xai/${rbd}/shapley?factor=${factor}`)

export const listarEstablecimientos = () =>
  pedir<RespuestaEstablecimientos>('/establecimientos')

export const obtenerObservacion = (rbd: string) =>
  pedir<Observacion>(`/establecimientos/${rbd}`)

export const obtenerRanking = (rbd: string) =>
  pedir<Ranking>(`/establecimientos/${rbd}/ranking`)

export const obtenerComposicion = () =>
  pedir<Composicion>('/salud/composicion')

/* -------------------------------------------------------------------------
 * Escenarios. La estimacion siempre viene del motor, nunca del navegador.
 * ---------------------------------------------------------------------- */

/** Curva de sensibilidad de UNA variable. */
export const simular = (rbd: string, variable: string, nPuntos = 25) =>
  pedir<Simulacion>('/xai/simular', {
    method: 'POST',
    body: JSON.stringify({ rbd, variable, n_puntos: nPuntos, variables: {} }),
  })

/** Indice estimado con VARIAS variables de gestion modificadas a la vez. */
export const evaluarEscenario = (rbd: string, variables: Record<string, number>) =>
  pedir<Prediccion>(`/prediccion/${rbd}/escenario`, {
    method: 'POST',
    body: JSON.stringify({ variables }),
  })

/* -------------------------------------------------------------------------
 * Asesor de gestion (cuanto 5).
 *
 * No usa `pedir`: apunta a otro servicio, en otro puerto. Reenvia el token de
 * la sesion en la cabecera porque el agente actua EN NOMBRE del usuario; asi
 * CTRL-04 protege al directivo y no a una cuenta de servicio compartida.
 * Un fallo aqui no debe parecer un fallo del sistema: el agente es retirable,
 * y el mensaje de error lo dice con esas palabras.
 * ---------------------------------------------------------------------- */

export async function consultarAsesor(
  rbd: string,
  texto: string,
  periodo?: string,
): Promise<RespuestaAsesor> {
  if (!sesion) throw new Error('Su sesion expiro. Vuelva a iniciar sesion.')

  let respuesta: Response
  try {
    respuesta = await fetch(`${BASE_ASESOR}/asesor/consulta`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sesion.token}`,
      },
      body: JSON.stringify({ rbd, texto, periodo: periodo ?? null, usuario: sesion.rol }),
    })
  } catch {
    throw new Error(
      `No fue posible conectar con el asesor en ${BASE_ASESOR}. El servicio del agente ` +
        'es una unidad de despliegue aparte: el tablero, el simulador y el reporte ' +
        'de explicabilidad siguen operativos aunque este apagado.',
    )
  }

  if (respuesta.status === 401) throw new Error('Su sesion expiro. Vuelva a iniciar sesion.')
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({ detail: respuesta.statusText }))
    throw new Error(cuerpo.detail ?? `Error ${respuesta.status}`)
  }
  return respuesta.json() as Promise<RespuestaAsesor>
}
