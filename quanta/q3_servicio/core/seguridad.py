"""Control de Acceso Basado en Roles — CTRL-04.

Principio de minimo privilegio: un director solo accede a los RBD bajo su
jurisdiccion legal. Un fallo aqui es fallo de la compuerta 2 del protocolo de
incorporacion del incremento, no una advertencia.

NOTA DE ALCANCE: la persistencia de usuarios vive en el esquema transaccional
de PostgreSQL. Este modulo trae un directorio en memoria para desarrollo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from q3_servicio.core.config import config

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


class Rol(str, Enum):
    SOSTENEDOR = "sostenedor"
    DIRECTIVO = "directivo"
    AUDITOR = "auditor"


@dataclass
class Usuario:
    usuario: str
    nombre: str
    rol: Rol
    rbds: list[str] = field(default_factory=list)

    def puede_ver(self, rbd: str) -> bool:
        if self.rol is Rol.AUDITOR:
            return True
        return str(rbd) in {str(r) for r in self.rbds}


# Directorio de desarrollo. En produccion: esquema app.usuario en PostgreSQL.
DIRECTORIO: dict[str, Usuario] = {
    "sostenedor.demo": Usuario("sostenedor.demo", "Sostenedor Demo", Rol.SOSTENEDOR, ["25520", "9012", "10156"]),
    "directora.demo": Usuario("directora.demo", "Directora Demo", Rol.DIRECTIVO, ["25520"]),
    "sagrado.demo": Usuario("sagrado.demo", "Sagrados Corazones de La Reina", Rol.DIRECTIVO, ["25520"]),
    "auditor.demo": Usuario("auditor.demo", "Auditoria", Rol.AUDITOR, []),
}


def emitir_token(usuario: Usuario) -> str:
    cfg = config()
    expira = datetime.now(timezone.utc) + timedelta(minutes=cfg.jwt_minutos_expiracion)
    carga = {"sub": usuario.usuario, "rol": usuario.rol.value, "exp": expira}
    return jwt.encode(carga, cfg.jwt_secret_key, algorithm=cfg.jwt_algoritmo)


def usuario_actual(token: str | None = Depends(oauth2)) -> Usuario:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales ausentes")
    cfg = config()
    try:
        carga = jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algoritmo])
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido o expirado") from exc
    usuario = DIRECTORIO.get(carga.get("sub", ""))
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no reconocido")
    return usuario


def exigir_jurisdiccion(rbd: str, usuario: Usuario) -> None:
    """CTRL-04. Devuelve 403, nunca 404: no se filtra la existencia del RBD."""
    if not usuario.puede_ver(rbd):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"El RBD {rbd} no pertenece a la jurisdiccion de {usuario.usuario}.",
        )
