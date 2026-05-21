# @track_context("api_setup.md")

import logging
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.router import api_router
from src.core.config import settings
from src.core.database import engine
from src.core.supabase_client import _jwks_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        logger.info("Fetching JWKS from Supabase at startup...")
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        _jwks_cache.update(response.json())
        logger.info(f"JWKS loaded successfully ({len(_jwks_cache.get('keys', []))} keys)")
    except Exception as e:
        logger.error(f"Failed to fetch JWKS at startup: {e}")
        raise

    try:
        logger.info("Running ANALYZE to update table statistics...")
        async with engine.connect() as conn:
            await conn.execute(text("ANALYZE"))
            await conn.commit()
        logger.info("ANALYZE completed successfully")
    except Exception as e:
        logger.warning(f"ANALYZE failed (non-critical): {e}")

    yield


app = FastAPI(
    title="Supabase Auth API",
    description="Production-ready authentication API with Supabase",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}
