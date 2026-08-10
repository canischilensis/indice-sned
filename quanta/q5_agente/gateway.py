"""Gateway hacia el servicio (Q3). Unico punto del cuanto 5 que habla HTTP.

Patron Gateway: encapsula el sistema externo y traduce sus codigos a errores del
dominio. El resto del cuanto 5 no sabe que existe HTTP, ni que existe FastAPI,
ni que el servicio devuelve 403 en lugar de 404.

Regla de arquitectura: este modulo NO importa q2_modelamiento ni q3_servicio. El
agente consulta las rutas publicadas como lo haria cualquier usuario, y por lo
tanto queda sometido a CTRL-04 igual que la interfaz.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

import httpx

from q5_agente.errores import (
    EstablecimientoNoEncontrado,
    FueraDeJurisdiccion,
    ParametroInvalido,
    ServicioNoDisponible,
    SesionExpirada,
)

_TRADUCCION = {
    401: SesionExpirada,
    403: FueraDeJurisdiccion,
    404: EstablecimientoNoEncontrado,
    422: ParametroInvalido,
    503: ServicioNoDisponible,
}


class PuertaDeServicio(Protocol):
    """Contrato minimo que las herramientas exigen. Permite dobles en pruebas."""

    def obtener(self, ruta: str, parametros: dict[str, Any] | None = None) -> dict: ...

    def enviar(self, ruta: str, cuerpo: dict[str, Any]) -> dict: ...


def cerrar_puerta(puerta: PuertaDeServicio) -> None:
    """Cierra la puerta si la implementacion sostiene una conexion.

    Los dobles de prueba no tienen nada que cerrar y no deben verse obligados a
    declarar un metodo vacio solo para satisfacer al llamador.
    """
    cerrar = getattr(puerta, "cerrar", None)
    if callable(cerrar):
        cerrar()


class ServicioSnedGateway:
    """Adaptador HTTP del servicio del Indice SNED.

    Dos modos de identidad, y la diferencia es de seguridad, no de comodidad:

    - **Credenciales propias** (`usuario` y `clave`): el agente se autentica como
      una cuenta de servicio. Sirve para la consola y para los trabajos por
      lotes, donde no hay un usuario detras.
    - **Token delegado** (`token`): el agente actua *en nombre del usuario* que
      inicio sesion en la interfaz, reenviando su credencial. Es el unico modo
      admisible cuando el agente se expone a un navegador: sin el, CTRL-04
      protegeria a la cuenta de servicio y no al directivo, y un usuario podria
      alcanzar establecimientos fuera de su jurisdiccion.
    """

    def __init__(
        self,
        base_url: str,
        usuario: str = "",
        clave: str = "",
        *,
        token: str | None = None,
        prefijo: str = "/api/v1",
        segundos_espera: float = 10.0,
        cliente: httpx.Client | None = None,
    ) -> None:
        if not token and not (usuario and clave):
            raise ValueError(
                "El gateway necesita un token delegado o un par usuario/clave propio."
            )
        self._base = base_url.rstrip("/")
        self._prefijo = prefijo
        self._usuario = usuario
        self._clave = clave
        self._token: str | None = token
        self._delegado = token is not None
        self._cliente = cliente or httpx.Client(timeout=segundos_espera)

    # --- sesion -----------------------------------------------------------

    def autenticar(self) -> str:
        if self._delegado:
            # Con identidad delegada no hay nada que negociar: el token es del
            # usuario y el agente no puede renovarlo por su cuenta.
            raise SesionExpirada(
                "La sesion del usuario expiro. Vuelva a iniciar sesion en la interfaz."
            )
        respuesta = self._intentar(
            lambda: self._cliente.post(
                f"{self._base}{self._prefijo}/auth/token",
                data={"username": self._usuario, "password": self._clave},
            )
        )
        if respuesta.status_code == 401:
            raise SesionExpirada("Credenciales invalidas para el servicio del indice.")
        respuesta.raise_for_status()
        self._token = respuesta.json()["access_token"]
        return self._token

    @property
    def _cabeceras(self) -> dict[str, str]:
        if self._token is None:
            self.autenticar()
        return {"Authorization": f"Bearer {self._token}"}

    # --- verbos -----------------------------------------------------------

    def obtener(self, ruta: str, parametros: dict[str, Any] | None = None) -> dict:
        cabeceras = self._cabeceras
        return self._resolver(
            self._intentar(
                lambda: self._cliente.get(
                    f"{self._base}{self._prefijo}{ruta}",
                    params={k: v for k, v in (parametros or {}).items() if v is not None},
                    headers=cabeceras,
                )
            )
        )

    def enviar(self, ruta: str, cuerpo: dict[str, Any]) -> dict:
        cabeceras = self._cabeceras
        return self._resolver(
            self._intentar(
                lambda: self._cliente.post(
                    f"{self._base}{self._prefijo}{ruta}",
                    json=cuerpo,
                    headers=cabeceras,
                )
            )
        )

    # --- traduccion de errores -------------------------------------------

    def _intentar(self, llamada: Callable[[], httpx.Response]) -> httpx.Response:
        """Traduce el fallo de transporte a una condicion del dominio.

        Sin esto, un servicio apagado sube como httpx.ConnectError hasta la
        consola y se ve como una traza. El agente debe decir que no puede
        responder, igual que cuando falta un artefacto.
        """
        try:
            return llamada()
        except httpx.TimeoutException as exc:
            raise ServicioNoDisponible(
                f"El servicio del indice no respondio dentro del tiempo previsto ({self._base})."
            ) from exc
        except httpx.TransportError as exc:
            raise ServicioNoDisponible(
                f"No fue posible conectar con el servicio del indice en {self._base}. "
                "Verifique que este levantado."
            ) from exc

    @staticmethod
    def _resolver(respuesta: httpx.Response) -> dict:
        if respuesta.status_code >= 400:
            detalle = ""
            try:
                detalle = str(respuesta.json().get("detail", ""))
            except (ValueError, AttributeError):
                detalle = respuesta.text[:200]
            error = _TRADUCCION.get(respuesta.status_code)
            if error is not None:
                raise error(detalle or f"El servicio respondio {respuesta.status_code}.")
            raise ServicioNoDisponible(
                f"El servicio respondio {respuesta.status_code}. {detalle}".strip()
            )
        return respuesta.json()

    def cerrar(self) -> None:
        """Cierra el cliente HTTP y sus conexiones.

        Debe llamarse. Dejarlo al recolector significa cerrar el socket desde un
        finalizador durante el apagado del interprete, que en Windows aparece
        como un "access violation" en un hilo secundario dentro de httpx: ruido
        alarmante para quien ejecuta la suite, y conexiones vivas de mas en el
        servicio, donde se construye una puerta por peticion.
        """
        self._cliente.close()

    def __enter__(self) -> ServicioSnedGateway:
        return self

    def __exit__(self, *_excepcion: object) -> None:
        self.cerrar()
