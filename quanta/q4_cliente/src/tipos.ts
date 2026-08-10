export interface FactorPredicho {
  codigo: string
  nombre: string
  peso: number
  valor: number
  aporte_al_indice: number
  es_acotado: boolean
  restriccion: string | null
}

export interface Prediccion {
  rbd: string
  indice: number
  factores: FactorPredicho[]
  estrategia: string
  version_modelo: string
  incertidumbre_mae: number | null
  advertencia: string
}

export interface Contribucion {
  variable: string
  etiqueta: string
  valor: number | null
  contribucion: number
  direccion: 'positiva' | 'negativa'
}

export interface Explicacion {
  rbd: string
  factor: string
  prediccion: number
  valor_base: number
  aditividad_verificada: boolean
  contribuciones: Contribucion[]
  lectura: string
}

export interface Simulacion {
  rbd: string
  variable: string
  etiqueta: string
  valores: number[]
  predicciones: number[]
  valor_actual: number | null
  prediccion_actual: number | null
  monotona: boolean
  advertencia_magnitud: string
}

export interface Alerta {
  tipo: string
  severidad: 'alta' | 'media' | 'informativa'
  titulo: string
  detalle: string
}

export interface Sesion {
  token: string
  rol: string
  rbds: string[]
}

/** Fila del listado que devuelve GET /establecimientos. */
export interface ResumenEstablecimiento {
  rbd: number | string
  bienio_premio: string | null
  cluster_codigo: number | null
  indicer: number | null
}

export interface RespuestaEstablecimientos {
  rol: string
  rbds: string[]
  origen: string
  detalle: ResumenEstablecimiento[]
}

export interface Ranking {
  rbd: string
  ciclo: string
  cluster_codigo: number
  indicer: number
  posicion_en_grupo: number
  n_grupo: number
  percentil: number
  sel: number | null
}

/** Diagnostico de cobertura tal como lo devuelve el servicio. */
export interface DiagnosticoCobertura {
  evaluable: boolean
  motivo?: string
  n_requeridas?: number
  n_disponibles?: number
  cobertura?: number
  faltantes?: string[]
  efecto?: string
}

/** GET /salud/composicion devuelve la composicion completa del servicio. */
export interface Composicion {
  estrategia: Record<string, unknown>
  repositorio: Record<string, unknown>
  reglas_de_alerta: string[]
  cobertura_de_variables: DiagnosticoCobertura
}

/** Observacion ancha de un establecimiento: nombres de variable como claves. */
export type Observacion = Record<string, number | string | null>

/* -------------------------------------------------------------------------
 * Asesor de gestion (cuanto 5). Vive en otro proceso y en otro puerto: si el
 * agente esta caido, las otras tres ventanas siguen funcionando.
 * ---------------------------------------------------------------------- */

/** Una invocacion de herramienta. Es la unidad de trazabilidad del agente. */
export interface LlamadaDeHerramienta {
  herramienta: string
  exito: boolean
  resumen: string
  milisegundos: number
}

export interface RespuestaAsesor {
  texto: string
  rechazada: boolean
  motivo_rechazo: string | null
  guardarrailes_aplicados: string[]
  llamadas: LlamadaDeHerramienta[]
  tokens_entrada: number
  tokens_salida: number
  costo_usd: number
}

/** Un intercambio de la conversacion, tal como se dibuja en pantalla. */
export interface Turno {
  id: number
  pregunta: string
  rbd: string
  respuesta: RespuestaAsesor | null
  error: string | null
}

/** Fila consolidada del tablero del sostenedor. */
export interface FilaTablero {
  rbd: string
  nombre: string
  matricula: number | null
  cluster: number | null
  bienio: string | null
  indicerOficial: number | null
  estimacion: number | null
  error: string | null
}
