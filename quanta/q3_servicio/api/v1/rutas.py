from fastapi import APIRouter

from q3_servicio.api.v1.routers import auth, establecimientos, explicabilidad, prediccion, salud

api_v1 = APIRouter()
api_v1.include_router(salud.router)
api_v1.include_router(auth.router)
api_v1.include_router(establecimientos.router)
api_v1.include_router(prediccion.router)
api_v1.include_router(explicabilidad.router)
