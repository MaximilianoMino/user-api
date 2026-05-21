import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException

from src.api.api import app
from src.core.messages import ErrorMessages
from src.api.dependencies import get_current_user


class TestGetMeEndpoint:
    """Tests for GET /api/v1/me endpoint"""

    @pytest.mark.asyncio
    async def test_get_me_no_token(self):
        """Test 1: No token provided returns 403"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403


class TestGetCurrentUser:
    """Tests for get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test 1: Valid token returns user data from public.usuario"""
        mock_user_data = {
            "user_id": 1,
            "nombre": "Test User",
            "email": "test@test.com",
            "telefono": "1234567890",
            "auth_user_id": "auth-user-123",
        }

        mock_auth_user = MagicMock()
        mock_auth_user.user = MagicMock()
        mock_auth_user.user.id = "auth-user-123"

        mock_client = MagicMock()
        mock_client.auth.get_user = MagicMock(return_value=mock_auth_user)

        mock_client.table.return_value.select.return_value.eq.return_value.execute = MagicMock(
            return_value=MagicMock(data=[mock_user_data])
        )

        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"

        result = await get_current_user(mock_credentials, mock_client)

        assert result["user_id"] == 1
        assert result["nombre"] == "Test User"
        assert result["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test 2: Invalid token raises HTTPException 401"""
        mock_client = MagicMock()
        mock_client.auth.get_user = MagicMock(side_effect=Exception("Invalid token"))

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_client)

        assert exc_info.value.status_code == 401
        assert ErrorMessages.INVALID_TOKEN in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_not_in_db(self):
        """Test 3: Valid token but user not in database raises HTTPException 401"""
        mock_auth_user = MagicMock()
        mock_auth_user.user = MagicMock()
        mock_auth_user.user.id = "auth-user-123"

        mock_client = MagicMock()
        mock_client.auth.get_user = MagicMock(return_value=mock_auth_user)

        mock_client.table.return_value.select.return_value.eq.return_value.execute = MagicMock(
            return_value=MagicMock(data=[])
        )

        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_client)

        assert exc_info.value.status_code == 401
        assert ErrorMessages.USER_NOT_FOUND in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_no_auth_user(self):
        """Test 4: Token with no user in auth response raises HTTPException 401"""
        mock_client = MagicMock()

        mock_auth_user = MagicMock()
        mock_auth_user.user = None
        mock_client.auth.get_user = MagicMock(return_value=mock_auth_user)

        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_client)

        assert exc_info.value.status_code == 401
        assert ErrorMessages.INVALID_TOKEN in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_auth_exception(self):
        """Test 5: Auth get_user raises exception raises HTTPException 401"""
        mock_client = MagicMock()
        mock_client.auth.get_user = MagicMock(side_effect=ValueError("Token expired"))

        mock_credentials = MagicMock()
        mock_credentials.credentials = "expired_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_client)

        assert exc_info.value.status_code == 401


class TestGetMeOrgInfoHandling:
    """Tests for get_me endpoint handling of None/missing org_info"""

    @pytest.mark.asyncio
    async def test_get_me_org_info_none(self):
        """Test 1: Test the org_info None handling logic directly"""
        from src.api.endpoints.auth import get_me
        from src.models.auth import OrganizacionBrief, MeResponse, UserProfile
        import logging

        mock_user = {
            "user_id": 1,
            "nombre": "Test User",
            "email": "test@test.com",
            "auth_user_id": "auth-user-123",
        }

        mock_orgs_result = MagicMock()
        mock_orgs_result.data = [
            {"org_id": 999, "rol": "administrador", "organizacion": None}
        ]

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute = MagicMock(
            return_value=mock_orgs_result
        )

        result = await get_me(mock_user, mock_supabase)

        assert result.user.user_id == 1
        assert len(result.organizaciones) == 1
        assert result.organizaciones[0].org_id == 999
        assert result.organizaciones[0].nombre == "Desconocida"
        assert result.organizaciones[0].tipo == "desconocido"

    @pytest.mark.asyncio
    async def test_get_me_org_info_missing(self):
        """Test 2: Test when organizacion key is missing entirely"""
        from src.api.endpoints.auth import get_me
        from src.models.auth import OrganizacionBrief, MeResponse, UserProfile
        import logging

        mock_user = {
            "user_id": 1,
            "nombre": "Test User",
            "email": "test@test.com",
            "auth_user_id": "auth-user-123",
        }

        mock_orgs_result = MagicMock()
        mock_orgs_result.data = [
            {"org_id": 888, "rol": "usuario"}
        ]

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute = MagicMock(
            return_value=mock_orgs_result
        )

        result = await get_me(mock_user, mock_supabase)

        assert result.user.user_id == 1
        assert len(result.organizaciones) == 1
        assert result.organizaciones[0].org_id == 888
        assert result.organizaciones[0].nombre == "Desconocida"
        assert result.organizaciones[0].tipo == "desconocido"