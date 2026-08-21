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

/** Fila consolidada del tablero del sostenedor. */
export interface FilaTablero {
  rbd: string
  nombre: string
  matricula: number | null
  cluster: number | null
  bienio: string | null
  indicerOficial: number | null
  estimacion: number | null
  /** Error absoluto medio del motor. Define la banda que se pinta junto a la
   *  estimacion: un numero solo se lee como exacto, y esta no lo es. */
  incertidumbre: number | null
  error: string | null
}
