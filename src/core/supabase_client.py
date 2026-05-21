# @track_context("config.md")

from typing import Any, Dict

from supabase import Client, create_client

from src.core.config import settings

# Global client instance to preserve PKCE state
_supabase_client: Client | None = None

# JWKS cache — populated once at startup via lifespan
_jwks_cache: Dict[str, Any] = {}


def get_supabase_client() -> Client:
    """Get Supabase client instance (singleton to preserve PKCE state)"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client
