"""Servicio HTTP del cuanto 5.

Unidad de despliegue propia: proceso separado del servicio del indice. Si este
proceso se apaga, el tablero, el simulador y el reporte de explicabilidad siguen
funcionando, porque ninguno de ellos depende del agente.

    uvicorn q5_agente.app:app --reload --app-dir quanta --port 8010
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from q5_agente.config import config_agente
from q5_agente.contrato import Consulta
from q5_agente.errores import ErrorDelAgente
from q5_agente.fabrica import crear_agente, crear_puerta
from q5_agente.gateway import PuertaDeServicio, cerrar_puerta


class SolicitudDeAsesoria(BaseModel):
    rbd: str = Field(..., description="Rol Base de Datos bajo jurisdiccion del usuario")
    texto: str = Field(..., min_length=3, max_length=2000)
    periodo: str | None = None
    usuario: str = "anonimo"


class LlamadaSalida(BaseModel):
    herramienta: str
    exito: bool
    resumen: str
    milisegundos: int


class RespuestaDeAsesoria(BaseModel):
    texto: str
    rechazada: bool
    motivo_rechazo: str | None = None
    guardarrailes_aplicados: list[str] = []
    llamadas: list[LlamadaSalida] = []
    tokens_entrada: int = 0
    tokens_salida: int = 0
    costo_usd: float = 0.0


app = FastAPI(
    title="Asesor de gestion del Indice SNED",
    version="0.1.0",
    description=(
        "Cuanto 5. Traduce y prioriza lo que el servicio del indice calcula. No computa el "
        "indice ni pondera factores: consulta las rutas publicadas como cualquier usuario."
    ),
)

_cfg = config_agente()
# Los origenes vienen de configuracion, no del codigo. Escritos a mano aqui, el
# servicio quedaba atado a que el cliente viviera en 127.0.0.1:5173: cierto en
# esta maquina y falso en cuanto el cliente se publique en otro puerto o en otro
# contenedor. Una direccion de red es configuracion de despliegue.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cfg.cors_origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _token_del_usuario(autorizacion: str | None) -> str:
    """Exige la credencial del usuario. No hay modo anonimo, a proposito.

    El agente actua **en nombre de quien pregunta**: reenvia su token al servicio
    del indice, de modo que CTRL-04 protege al directivo y no a una cuenta de
    servicio compartida. Sin esta delegacion, cualquier usuario de la interfaz
    alcanzaria todos los establecimientos de la jurisdiccion del agente.
    """
    if not autorizacion or not autorizacion.lower().startswith("bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Falta la credencial del usuario. Inicie sesion en la interfaz.",
        )
    return autorizacion.split(" ", 1)[1].strip()


@contextmanager
def puerta_para(token: str) -> Iterator[PuertaDeServicio]:
    """Puerta por peticion, cerrada al terminar.

    Un agente por peticion implica un cliente HTTP por peticion, y eso obliga a
    cerrarlo: sin esto, cada consulta dejaba conexiones vivas hasta que el
    recolector pasara. Es el precio de no compartir identidad, y se paga aqui.
    """
    puerta = crear_puerta(token=token)
    try:
        yield puerta
    finally:
        cerrar_puerta(puerta)


@app.get("/salud")
def salud() -> dict[str, Any]:
    return {
        "estado": "operativo",
        "proveedor": _cfg.agente_proveedor,
        "servicio_indice": _cfg.agente_base_url,
        "identidad": "delegada: el agente reenvia el token del usuario (CTRL-04)",
        "guardarrailes": {
            "G-01": "sanitizacion de parametros",
            "G-02": "cifras fundadas en herramientas" if _cfg.agente_guardarrail_cifras else "off",
            "G-03": "sin promesas de retorno" if _cfg.agente_guardarrail_promesas else "off",
        },
    }


@app.post("/asesor/consulta", response_model=RespuestaDeAsesoria)
def consultar(
    solicitud: SolicitudDeAsesoria,
    authorization: str | None = Header(default=None),
) -> RespuestaDeAsesoria:
    """Responde en nombre del usuario que envia su credencial en la cabecera."""
    token = _token_del_usuario(authorization)
    with puerta_para(token) as puerta:
        asesor = crear_agente(puerta=puerta, token=token)
        try:
            respuesta = asesor.asesorar(
                Consulta(
                    texto=solicitud.texto,
                    rbd=solicitud.rbd,
                    periodo=solicitud.periodo,
                    usuario=solicitud.usuario,
                )
            )
        except ErrorDelAgente as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return RespuestaDeAsesoria(
        texto=respuesta.texto,
        rechazada=respuesta.rechazada,
        motivo_rechazo=respuesta.motivo_rechazo,
        guardarrailes_aplicados=respuesta.guardarrailes_aplicados,
        llamadas=[
            LlamadaSalida(
                herramienta=ll.herramienta,
                exito=ll.exito,
                resumen=ll.resumen,
                milisegundos=ll.milisegundos,
            )
            for ll in respuesta.llamadas
        ],
        tokens_entrada=respuesta.uso.tokens_entrada,
        tokens_salida=respuesta.uso.tokens_salida,
        costo_usd=respuesta.uso.costo_usd,
    )
