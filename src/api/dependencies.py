# @track_context("dependencies.md")

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import (
    TTLCache,
    user_cache,
    org_cache,
    cache_key_user,
    cache_key_org,
)
from src.core.supabase_client import _jwks_cache
from src.core.config import settings
from src.core.database import get_db
from src.core.messages import ErrorMessages, LogMessages
from src.models.usuario import Usuario
from src.models.usuario_organizacion_rol import UsuarioOrganizacionRol
from src.repositories.lote_repository import LoteRepository
from src.repositories.evidencia_repository import EvidenciaRepository
from src.repositories.documento_repository import DocumentoRepository
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_signing_key(token: str) -> Dict[str, Any]:
    """Extract the correct signing key from pre-loaded JWKS using token's kid."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header (missing kid)",
            )

        if not _jwks_cache:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWKS not loaded",
            )

        for key in _jwks_cache.get("keys", []):
            if key.get("kid") == kid:
                return key

        logger.warning(f"Signing key not found for kid={kid}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token (signing key not found)",
        )

    except HTTPException:
        raise
    except JWTError as err:
        logger.warning(LogMessages.JWT_VALIDATION_FAILED.format(error=err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INVALID_TOKEN,
        ) from err


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract current authenticated user from public.usuario.
    Decodes JWT locally using pre-loaded JWKS (zero HTTP calls) and queries user via SQLAlchemy.
    Results are cached for 5 minutes.
    """
    token = credentials.credentials
    cache_key = cache_key_user(token)

    cached = user_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "RS256")
        key = get_signing_key(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
        )
        auth_user_id = payload.get("sub")
        if not auth_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessages.INVALID_TOKEN,
            )
    except HTTPException:
        raise
    except JWTError as err:
        logger.warning(LogMessages.JWT_VALIDATION_FAILED.format(error=err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INVALID_TOKEN,
        ) from err

    result = await db.execute(
        select(Usuario).where(Usuario.auth_user_id == auth_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.USER_NOT_FOUND,
        )

    user_data = {
        "user_id": user.user_id,
        "nombre": user.nombre,
        "email": user.email,
        "telefono": user.telefono,
        "auth_user_id": str(user.auth_user_id),
    }

    user_cache.set(cache_key, user_data)
    return user_data


def get_auth_service() -> AuthService:
    return AuthService()


async def get_org_id(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_org_id: int = Header(alias="X-Org-Id"),
) -> int:
    """
    Validate that user belongs to the organization from X-Org-Id header.
    Uses SQLAlchemy instead of Supabase REST API.
    Results are cached for 5 minutes.
    """
    if not x_org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.ORG_ID_MISSING,
        )

    user_id = current_user["user_id"]
    cache_key = cache_key_org(user_id, x_org_id)

    cached = org_cache.get(cache_key)
    if cached is not None:
        return x_org_id

    result = await db.execute(
        select(UsuarioOrganizacionRol).where(
            UsuarioOrganizacionRol.user_id == user_id,
            UsuarioOrganizacionRol.org_id == x_org_id,
        )
    )

    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.ORG_ID_UNAUTHORIZED,
        )

    org_cache.set(cache_key, x_org_id)
    return x_org_id


async def get_lote_repository(db: AsyncSession = Depends(get_db)) -> LoteRepository:
    """Dependency to get LoteRepository instance."""
    return LoteRepository(db)


async def get_evidencia_repository(db: AsyncSession = Depends(get_db)) -> EvidenciaRepository:
    """Dependency to get EvidenciaRepository instance."""
    return EvidenciaRepository(db)


async def get_documento_repository(db: AsyncSession = Depends(get_db)) -> DocumentoRepository:
    """Dependency to get DocumentoRepository instance."""
    return DocumentoRepository(db)
