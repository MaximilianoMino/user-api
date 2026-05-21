import pytest
import os
import base64
import json
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from src.api import dependencies


def create_valid_jwt(header_payload: dict, signature: str = "dGVzdA==") -> str:
    """Crea un JWT válido para testing"""
    header_b64 = base64.urlsafe_b64encode(json.dumps(header_payload).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps({"sub": "user123", "aud": "authenticated"}).encode()).decode().rstrip('=')
    return f"{header_b64}.{payload_b64}.{signature}"


class TestGetJwks:
    """Tests para la función get_jwks"""

    @patch('src.api.dependencies.requests.get')
    def test_get_jwks_success(self, mock_get):
        """Test 1: Obtener JWKS exitosamente"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": [{"kid": "key1", "kty": "RSA"}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Limpiar cache
        dependencies.get_jwks.cache_clear()
        
        result = dependencies.get_jwks()
        
        assert "keys" in result
        assert len(result["keys"]) == 1
        dependencies.get_jwks.cache_clear()

    @patch('src.api.dependencies.requests.get')
    def test_get_jwks_http_error(self, mock_get):
        """Test 2: Error HTTP al obtener JWKS"""
        mock_get.side_effect = Exception("Connection error")
        
        dependencies.get_jwks.cache_clear()
        
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_jwks()
        
        assert exc_info.value.status_code == 503
        assert "Unable to fetch authentication keys" in exc_info.value.detail
        dependencies.get_jwks.cache_clear()

    @patch('src.api.dependencies.requests.get')
    def test_get_jwks_cached(self, mock_get):
        """Test 3: JWKS se cachea correctamente"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        dependencies.get_jwks.cache_clear()
        
        # Llamar dos veces
        result1 = dependencies.get_jwks()
        result2 = dependencies.get_jwks()
        
        # Solo debe haber una llamada a requests.get
        assert mock_get.call_count == 1
        dependencies.get_jwks.cache_clear()


class TestGetSigningKey:
    """Tests para la función get_signing_key"""

    @patch('src.api.dependencies.get_jwks')
    def test_get_signing_key_found(self, mock_get_jwks):
        """Test 1: Encontrar clave de firma por kid"""
        mock_get_jwks.return_value = {
            "keys": [
                {"kid": "key1", "kty": "RSA", "alg": "RS256"},
                {"kid": "key2", "kty": "RSA", "alg": "RS256"}
            ]
        }
        
        # Crear un token válido con kid en el header
        mock_token = create_valid_jwt({"alg": "RS256", "kid": "key1", "typ": "JWT"})
        
        result = dependencies.get_signing_key(mock_token)
        
        assert result["kid"] == "key1"

    @patch('src.api.dependencies.get_jwks')
    def test_get_signing_key_not_found(self, mock_get_jwks):
        """Test 2: Clave de firma no encontrada"""
        mock_get_jwks.return_value = {"keys": [{"kid": "other_key"}]}
        
        mock_token = create_valid_jwt({"alg": "RS256", "kid": "nonexistent", "typ": "JWT"})
        
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_signing_key(mock_token)
        
        assert exc_info.value.status_code == 401
        assert "signing key not found" in exc_info.value.detail

    def test_get_signing_key_missing_kid(self):
        """Test 3: Token sin kid en header"""
        # Token con header que no tiene kid
        mock_token = create_valid_jwt({"alg": "RS256", "typ": "JWT"})  # Sin kid
        
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_signing_key(mock_token)
        
        assert exc_info.value.status_code == 401
        assert "missing kid" in exc_info.value.detail


class TestValidateJwtToken:
    """Tests para la función validate_jwt_token"""

    @patch('src.api.dependencies.get_signing_key')
    def test_validate_jwt_token_success(self, mock_get_key):
        """Test 1: Validar token exitosamente"""
        mock_key = {"kid": "key1", "kty": "RSA", "alg": "RS256"}
        mock_get_key.return_value = mock_key
        
        # Crear un token válido
        mock_token = create_valid_jwt({"alg": "RS256", "kid": "key1", "typ": "JWT"})
        
        with patch('src.api.dependencies.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": "user123", "aud": "authenticated"}
            
            result = dependencies.validate_jwt_token(mock_token)
            
            assert result == "user123"

    @patch('src.api.dependencies.get_signing_key')
    def test_validate_jwt_token_invalid(self, mock_get_key):
        """Test 2: Token inválido"""
        mock_get_key.side_effect = HTTPException(status_code=401, detail="Invalid token")
        
        mock_token = create_valid_jwt({"alg": "RS256", "kid": "key1", "typ": "JWT"})
        
        with pytest.raises(HTTPException) as exc_info:
            dependencies.validate_jwt_token(mock_token)
        
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Tests para la función get_current_user"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test 1: Obtener usuario actual exitosamente"""
        mock_user_data = {
            "user_id": 1,
            "nombre": "Test User",
            "email": "test@test.com",
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
        mock_credentials.credentials = "mock_token"

        result = await dependencies.get_current_user(mock_credentials, mock_client)

        assert result["user_id"] == 1
        assert result["nombre"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test 2: Token inválido"""
        mock_client = MagicMock()
        mock_client.auth.get_user = MagicMock(side_effect=Exception("Invalid token"))

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"

        with pytest.raises(HTTPException) as exc_info:
            await dependencies.get_current_user(mock_credentials, mock_client)

        assert exc_info.value.status_code == 401


class TestGetAuthService:
    """Tests para la función get_auth_service"""

    def test_get_auth_service_returns_auth_service(self):
        """Test 1: Retorna una instancia de AuthService"""
        from src.services.auth_service import AuthService
        
        result = dependencies.get_auth_service()
        
        assert isinstance(result, AuthService)


class TestHTTPBearer:
    """Tests para el esquema de seguridad HTTPBearer"""

    def test_security_is_httpbearer(self):
        """Test 1: security es una instancia de HTTPBearer"""
        from fastapi.security import HTTPBearer
        
        assert isinstance(dependencies.security, HTTPBearer)