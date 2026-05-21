# @track_context("api_setup.md")

from fastapi import APIRouter

from src.api.endpoints import auth, lotes, muestras, analisis, fichas, public, evidencias, catalogos, parametros, documentos, ia

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(lotes.router, prefix="", tags=["lotes"])
api_router.include_router(muestras.router, prefix="", tags=["muestras"])
api_router.include_router(analisis.router, prefix="", tags=["analisis"])
api_router.include_router(fichas.router, prefix="", tags=["fichas"])
api_router.include_router(public.router, prefix="", tags=["public"])
api_router.include_router(evidencias.router, prefix="", tags=["evidencias"])
api_router.include_router(catalogos.router, prefix="", tags=["catálogos"])
api_router.include_router(parametros.router, prefix="", tags=["parámetros"])
api_router.include_router(documentos.router, prefix="", tags=["documentos"])
api_router.include_router(ia.router, prefix="", tags=["ia"])
