from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from q3_servicio.core.seguridad import DIRECTORIO, Usuario, emitir_token, usuario_actual

router = APIRouter(prefix="/auth", tags=["autenticacion"])

# Credenciales de desarrollo. En produccion: hash en el esquema app de PostgreSQL.
CLAVE_DEMO = "demo"


@router.post("/token")
def token(datos: OAuth2PasswordRequestForm = Depends()) -> dict:
    usuario = DIRECTORIO.get(datos.username)
    if usuario is None or datos.password != CLAVE_DEMO:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return {
        "access_token": emitir_token(usuario),
        "token_type": "bearer",
        "rol": usuario.rol.value,
        "rbds": usuario.rbds,
    }


@router.get("/yo")
def yo(usuario: Usuario = Depends(usuario_actual)) -> dict:
    return {
        "usuario": usuario.usuario,
        "nombre": usuario.nombre,
        "rol": usuario.rol.value,
        "rbds": usuario.rbds,
    }
