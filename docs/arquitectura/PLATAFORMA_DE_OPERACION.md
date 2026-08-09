# Diseño de la plataforma de operación

Identificador del documento: **PO-SNED-01**

Define dónde se ejecuta cada parte del sistema, con la distribución de operaciones en
**servidores separados de base de datos y de aplicación**. Se describen dos entornos: el de
desarrollo, que es el que está efectivamente en marcha, y el de operación previsto.

---

## 1. Principio de distribución

La separación entre servidor de datos y servidor de aplicación no es un adorno de diagrama:
responde a tres necesidades del dominio.

| Necesidad | Consecuencia |
|-----------|--------------|
| El dato del índice tiene consecuencia monetaria y debe respaldarse y auditarse con reglas propias | La base vive en un servidor con su propio ciclo de respaldo y su propia superficie de acceso |
| El servidor de aplicación mantiene en memoria 145 MB de artefactos (registro completo: 209 MiB) | Su dimensionamiento se rige por memoria, no por almacenamiento |
| La interfaz se compila a archivos estáticos | No requiere proceso propio y puede servirse desde el borde |

Consecuencia directa: **el servidor de aplicación es reemplazable y sin estado persistente**.
Todo lo que sobrevive a un reinicio está en la base o en el registro de artefactos.

## 2. Entorno de operación previsto

Representacion grafica: `docs/diagramas/06_despliegue.png`.


```
                         Internet
                             │
                        ┌────▼─────┐
                        │  HTTPS   │
                        └────┬─────┘
                             │
              ┌──────────────▼───────────────┐
              │  Nodo de borde / estáticos   │
              │  Interfaz compilada (Q4)     │
              │  HTML, JS, CSS               │
              └──────────────┬───────────────┘
                             │ XHR  /api/v1/*
              ┌──────────────▼───────────────┐
              │  SERVIDOR DE APLICACIÓN      │
              │                              │
              │  uvicorn + FastAPI (Q3)      │
              │  motor predictivo (Q2)       │
              │  registro de artefactos      │
              │                              │
              │  4 vCPU · 8 GB RAM · 20 GB   │
              │  sin estado persistente      │
              └──────────────┬───────────────┘
                             │ TCP 5432, red privada
              ┌──────────────▼───────────────┐
              │  SERVIDOR DE BASE DE DATOS   │
              │                              │
              │  PostgreSQL 16               │
              │  38 tablas · 4 esquemas      │
              │  ≈ 838.000 filas             │
              │                              │
              │  2 vCPU · 8 GB RAM · 50 GB   │
              │  respaldo diario             │
              └──────────────────────────────┘

              ┌──────────────────────────────┐
              │  ESTACIÓN DE INGESTA (Q1)    │
              │  proceso por lotes, bianual  │
              │  escribe parquet y carga BD  │
              └──────────────────────────────┘
```

### Asignación de responsabilidades

| Nodo | Contiene | No contiene |
|------|----------|-------------|
| Nodo de borde | Interfaz compilada, sin lógica de negocio | Ninguna credencial, ninguna regla de cálculo |
| Servidor de aplicación | Cuantos 2 y 3, artefactos serializados | Datos crudos; archivos de fuente pública |
| Servidor de base de datos | Los cuatro esquemas y las vistas | Código de aplicación |
| Estación de ingesta | Cuanto 1 y los archivos crudos | Nada expuesto a la red pública |

## 3. Dimensionamiento y su justificación

> **El dimensionamiento es una propuesta, no una restricción medida.** Las cifras de esta sección
> son un punto de partida derivado del consumo observado, no un límite impuesto por infraestructura
> existente ni un techo verificado en carga. Ninguna decisión de arquitectura de este proyecto se
> justifica por una restricción de hardware: el descarte de microservicios se sostiene por baja
> concurrencia y ciclo bianual (ver `ARQUITECTURA_AD_HOC.md`, sección 1).
>
> **Unidades.** El registro de artefactos ocupa **209 MiB** en disco, que se redondea a **210 MB**
> en el resto de la documentación. De ese total, el motor desagregado —el que sirve la interfaz—
> carga **145 MB**; los 65 MB restantes son el bosque aleatorio de comparación y la red neuronal
> del banco de pruebas, que no se materializan nunca.



| Recurso | Valor | Por qué |
|---------|-------|---------|
| Memoria del servidor de aplicación | 8 GB | El motor desagregado carga **145 MB** de artefactos, no los 210 MB del registro completo: 65 MB corresponden a modelos de comparación que nunca se materializan. El margen restante cubre el explicador de Shapley, que construye estructuras intermedias |
| CPU del servidor de aplicación | 4 vCPU | La simulación ejecuta 54 inferencias por llamada; es el pico de cómputo del sistema |
| Almacenamiento de la base | 50 GB | ≈ 838.000 filas más índices, vista materializada y margen para dos ciclos adicionales |
| Memoria de la base | 8 GB | La vista de ordenamiento intragrupo recorre 54.298 filas por consulta; conviene que quepa en memoria compartida |

## 4. Comunicación y puertos

| Origen | Destino | Protocolo | Puerto | Exposición |
|--------|---------|-----------|--------|-----------|
| Navegador | Nodo de borde | HTTPS | 443 | Pública |
| Navegador | Servidor de aplicación | HTTPS | 443 | Pública, restringida por CORS al origen de la interfaz |
| Servidor de aplicación | Base de datos | TCP/PostgreSQL | 5432 | **Red privada. Nunca pública** |
| Estación de ingesta | Base de datos | TCP/PostgreSQL | 5432 | Red privada |

El origen permitido para peticiones entre dominios se declara en configuración
(`api_cors_origins`), no en código.

## 5. Configuración por entorno

Toda la configuración es externa y se resuelve por variables de entorno. El código no contiene
ningún valor de despliegue.

| Variable | Desarrollo | Operación |
|----------|-----------|-----------|
| `DATABASE_URL` | `postgresql+psycopg://sned:...@localhost:5432/indice_sned` | Cadena hacia el servidor de datos privado |
| `REPOSITORIO_DATOS` | `postgres` (o `parquet` para demostrar sin base) | `postgres` |
| `API_CORS_ORIGINS` | `http://localhost:5173` | Origen del nodo de borde |
| `JWT_SECRET_KEY` | valor de desarrollo, declarado inseguro en el propio código | Secreto gestionado fuera del repositorio |
| `JWT_MINUTOS_EXPIRACION` | 480 | A definir por política de sesión |
| `API_ENTORNO` | `desarrollo` | `produccion` |
| `MOTOR_POR_DEFECTO` | `desagregado` | `desagregado` |

## 6. Entorno de desarrollo efectivamente en marcha

Es el que está operando hoy y el que reproduce el manual de instalación.

| Componente | Cómo corre | Puerto |
|-----------|-----------|--------|
| PostgreSQL 16 | Servicio nativo en Windows | 5432 |
| Servidor de aplicación | `uvicorn q3_servicio.main:app --reload --app-dir quanta` | 8000 |
| Interfaz | `npm run dev` sobre Vite | 5173 |

Las tres piezas conviven en una misma máquina, pero **se comunican exclusivamente por los
mismos protocolos que en operación**. Esa es la propiedad que hace del desarrollo una prueba
válida del despliegue: no hay atajo de memoria compartida entre cuantos.

## 7. Modo de contingencia sin base de datos

El sistema conserva deliberadamente el adaptador de parquet. Fijando `REPOSITORIO_DATOS=parquet`
el servicio opera sin base de datos alguna, leyendo los archivos columnares.

Existe por tres razones, y ninguna es nostalgia:

1. **Demostración** — el sistema se puede exhibir sin infraestructura.
2. **Verificación** — sin un segundo adaptador no hay contra qué comparar; la prueba de paridad
   dejaría de existir.
3. **Contingencia** — una caída del servidor de datos degrada el servicio a solo lectura sobre
   parquet, en vez de interrumpirlo.

## 8. Respaldo y recuperación

| Elemento | Estrategia | Frecuencia | Recuperación |
|----------|-----------|-----------|--------------|
| Base de datos | Volcado lógico completo | Diaria | Restaurar y volver a crear las vistas |
| Artefactos de modelo | Copia versionada fuera del repositorio | Por publicación | Reponer el directorio del registro |
| Esquema | Versionado en el repositorio | Por cambio | Reejecutar los archivos de esquema en orden |
| Datos crudos | Redescargables desde la fuente pública | — | Procedimiento en `docs/FUENTES.md` |

El esquema es reconstruible desde el repositorio y la carga es idempotente: reejecutar la carga
sobre una base ya poblada no duplica filas. Esa es la propiedad que convierte la recuperación
en un procedimiento y no en una improvisación.

## 9. Lo que esta plataforma no incluye

| Elemento | Estado | Motivo |
|----------|--------|--------|
| Orquestación de contenedores | Fuera de alcance | Un servicio, un motor de datos, cadencia bianual |
| Reentrenamiento automatizado | Fuera de alcance | ADR-003 |
| Alta disponibilidad de la base | No implementada | Requisito de negocio no establecido |
| Almacén de secretos | No implementado | La clave de firma vive en variable de entorno; declarado como deuda |
