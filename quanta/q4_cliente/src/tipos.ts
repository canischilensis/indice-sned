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
