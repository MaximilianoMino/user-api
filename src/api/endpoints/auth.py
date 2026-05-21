# @track_context("auth_endpoints.md")

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from supabase import Client, ClientOptions, create_client

from src.api.dependencies import get_auth_service, get_current_user, security
from src.core.config import settings
from src.core.constants import Supabase
from src.core.messages import ErrorMessages, SuccessMessages
from src.core.supabase_client import get_supabase_client
from src.models.auth import (
    AuthResponse,
    MeResponse,
    OAuthCallbackRequest,
    OAuthLoginRequest,
    OAuthResponse,
    PasswordResetRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserProfile,
    UserResponse,
)
from src.services.auth_service import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


def handle_auth_error(e: Exception) -> HTTPException:
    """
    Convert auth errors to appropriate HTTP exceptions

    Args:
        e: Exception from auth operation

    Returns:
        HTTPException with appropriate status code and message
    """
    if isinstance(e, ValueError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Authentication error: {e!s}",
    )


def format_auth_response(result: dict[str, Any]) -> AuthResponse:
    """
    Format Supabase auth result into standardized response

    Args:
        result: Raw result from Supabase auth operation

    Returns:
        Formatted auth response with user and token data
    """
    # Use pre-extracted full_name if available, otherwise extract safely
    full_name = result["user"].get("full_name", "")
    if not full_name:
        # Fallback: safely handle user_metadata which might be string or dict for OAuth users
        user_metadata = result["user"]["user_metadata"]
        if isinstance(user_metadata, dict):
            full_name = user_metadata.get(Supabase.FULL_NAME_FIELD, "")

    user_response = UserResponse(
        id=result["user"]["id"],
        email=result["user"]["email"],
        full_name=full_name,
        created_at=result["user"]["created_at"],
    )

    # Handle optional session data
    token_response = TokenResponse(
        access_token="",
        refresh_token="",
        token_type="bearer",
    )

    # Safely handle session data which might be dict or other type
    session_data = result.get("session")
    if (
        session_data
        and isinstance(session_data, dict)
        and session_data.get("access_token")
    ):
        token_response = TokenResponse(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"],
            token_type="bearer",
        )

    return AuthResponse(user=user_response, token=token_response)


@router.post(
    "/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    user_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> SignupResponse:
    """Register a new user account"""
    try:
        result = await auth_service.signup(user_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise handle_auth_error(e) from e


@router.post("/login", response_model=AuthResponse)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Log in with email and password"""
    try:
        result = await auth_service.login(user_data)
        return format_auth_response(result)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INVALID_CREDENTIALS,
        ) from None
    except Exception as e:
        raise handle_auth_error(e) from e


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Log out the current user"""
    try:
        if not token.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessages.INVALID_TOKEN,
            )

        success = await auth_service.logout(token.credentials)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorMessages.LOGOUT_FAILED,
            )

        return {"message": SuccessMessages.LOGOUT_SUCCESS}
    except Exception as e:
        raise handle_auth_error(e) from e


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Request a password reset"""
    try:
        await auth_service.request_password_reset(request.email)
        return {"message": SuccessMessages.PASSWORD_RESET_SENT}
    except Exception as e:
        raise handle_auth_error(e) from e


@router.get("/session-check", status_code=status.HTTP_200_OK)
async def session_check(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Check if the current session is valid"""
    return {"valid": True, "user_id": current_user["user_id"]}


@router.post("/oauth/login", response_model=OAuthResponse)
async def oauth_login(
    request: OAuthLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> OAuthResponse:
    """Initiate Google OAuth login flow"""
    try:
        result = await auth_service.oauth_login(request.provider, request.redirect_url)
        return OAuthResponse(auth_url=result["auth_url"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise handle_auth_error(e) from e


@router.post("/oauth/callback", response_model=AuthResponse)
async def oauth_callback(
    request: OAuthCallbackRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Handle Google OAuth callback and exchange code for tokens"""
    try:
        result = await auth_service.handle_oauth_callback(
            request.provider, request.code, request.redirect_url
        )
        return format_auth_response(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise handle_auth_error(e) from e


@router.get("/me", response_model=MeResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
) -> MeResponse:
    """
    Obtiene el perfil del usuario autenticado y sus organizaciones.
    """
    user_client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=ClientOptions(headers={"Authorization": f"Bearer {credentials.credentials}"})
    )

    orgs_result = user_client.table("usuario_organizacion_rol").select(
        "org_id, rol, organizacion(nombre, tipo)"
    ).eq("user_id", current_user["user_id"]).execute()

    organizaciones = []
    for row in (orgs_result.data or []):
        org_info = row.get("organizacion")
        if org_info is None:
            logger.warning(f"Organización no encontrada para org_id={row['org_id']}")
            nombre_org = "Desconocida"
            tipo_org = "desconocido"
        else:
            nombre_org = org_info.get("nombre", "")
            tipo_org = org_info.get("tipo", "")
        
        organizaciones.append(
            {
                "org_id": row["org_id"],
                "nombre": nombre_org,
                "tipo": tipo_org,
                "rol": row["rol"],
            }
        )

    return MeResponse(
        user=UserProfile(
            user_id=current_user["user_id"],
            nombre=current_user["nombre"],
            email=current_user["email"],
            telefono=current_user.get("telefono"),
        ),
        organizaciones=organizaciones,
    )
