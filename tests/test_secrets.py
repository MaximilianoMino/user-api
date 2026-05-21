import pytest
import os
from unittest.mock import MagicMock, patch
from src.core import secrets


class TestGetSecret:
    """Tests para la función get_secret"""

    @patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"})
    @patch('src.core.secrets.secretmanager.SecretManagerServiceClient')
    def test_get_secret_success(self, mock_client_class):
        """Test 1: Obtener secreto exitosamente de GSM"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.payload.data.decode.return_value = "secret_value_123"
        mock_client.access_secret_version.return_value = mock_response
        
        # Limpiar cache para permitir nueva ejecución
        secrets.get_secret.cache_clear()
        
        result = secrets.get_secret("SUPABASE_URL", "test-project")
        
        assert result == "secret_value_123"
        secrets.get_secret.cache_clear()

    @patch.dict(os.environ, {}, clear=True)
    def test_get_secret_no_project_id_returns_empty(self):
        """Test 2: Retorna vacío cuando GCP_PROJECT_ID no está definido (se captura la excepción)"""
        secrets.get_secret.cache_clear()
        
        # El ValueError se captura internamente y se retorna el fallback (empty string)
        result = secrets.get_secret("SUPABASE_URL")
        
        assert result == ""
        secrets.get_secret.cache_clear()

    @patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"})
    @patch('src.core.secrets.secretmanager.SecretManagerServiceClient')
    def test_get_secret_fallback_to_env(self, mock_client_class):
        """Test 3: Fallback a variable de entorno cuando GSM falla"""
        mock_client_class.return_value.access_secret_version.side_effect = Exception("GSM Error")
        
        with patch.dict(os.environ, {"SUPABASE_URL": "fallback_url"}):
            secrets.get_secret.cache_clear()
            
            result = secrets.get_secret("SUPABASE_URL", "test-project")
            
            assert result == "fallback_url"
            secrets.get_secret.cache_clear()

    @patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"})
    @patch('src.core.secrets.secretmanager.SecretManagerServiceClient')
    def test_get_secret_fallback_empty_when_no_env(self, mock_client_class):
        """Test 4: Fallback a string vacío cuando no hay variable de entorno"""
        mock_client_class.return_value.access_secret_version.side_effect = Exception("GSM Error")
        
        secrets.get_secret.cache_clear()
        
        result = secrets.get_secret("NON_EXISTENT_SECRET", "test-project")
        
        assert result == ""
        secrets.get_secret.cache_clear()


class TestLoadSecretsFromGsm:
    """Tests para la función load_secrets_from_gsm"""

    @patch('src.core.secrets.get_secret')
    @patch.dict(os.environ, {}, clear=True)
    def test_load_secrets_success(self, mock_get_secret):
        """Test 1: Cargar secretos exitosamente"""
        mock_get_secret.return_value = "secret_value"
        
        secrets.load_secrets_from_gsm()
        
        # Verificar que se llamaron los secretos requeridos
        assert mock_get_secret.call_count == 3  # SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET

    @patch.dict(os.environ, {"SUPABASE_URL": "already_set", "SUPABASE_KEY": "key_val", "SUPABASE_JWT_SECRET": "jwt_val"}, clear=False)
    @patch('src.core.secrets.get_secret')
    def test_load_secrets_skips_existing(self, mock_get_secret):
        """Test 2: No cargar secretos que ya existen en el entorno"""
        # No necesita return_value porque get_secret no debería ser llamado
        # cuando la variable ya existe en el entorno
        
        # La función debería ejecutarse sin errores
        secrets.load_secrets_from_gsm()
        
        # Verificar que get_secret NO fue llamado (porque las vars ya existen)
        mock_get_secret.assert_not_called()

    @patch('src.core.secrets.get_secret')
    @patch.dict(os.environ, {}, clear=True)
    def test_load_secrets_empty_value_warning(self, mock_get_secret):
        """Test 3: Advertencia cuando el secreto está vacío"""
        mock_get_secret.return_value = ""
        
        with patch('src.core.secrets.logger') as mock_logger:
            secrets.load_secrets_from_gsm()
            
            # Verificar que se emitió warning para secreto vacío
            assert mock_logger.warning.called


class TestShouldUseGsm:
    """Tests para la función should_use_gsm"""

    @patch.dict(os.environ, {"USE_GSM": "true"})
    def test_should_use_gsm_true(self):
        """Test 1: Retorna True cuando USE_GSM=true"""
        assert secrets.should_use_gsm() is True

    @patch.dict(os.environ, {"USE_GSM": "1"})
    def test_should_use_gsm_1(self):
        """Test 2: Retorna True cuando USE_GSM=1"""
        assert secrets.should_use_gsm() is True

    @patch.dict(os.environ, {"USE_GSM": "t"})
    def test_should_use_gsm_t(self):
        """Test 3: Retorna True cuando USE_GSM=t"""
        assert secrets.should_use_gsm() is True

    @patch.dict(os.environ, {"USE_GSM": "TRUE"})
    def test_should_use_gsm_uppercase(self):
        """Test 4: Retorna True cuando USE_GSM=TRUE (case insensitive)"""
        assert secrets.should_use_gsm() is True

    @patch.dict(os.environ, {"USE_GSM": "false"})
    def test_should_use_gsm_false(self):
        """Test 5: Retorna False cuando USE_GSM=false"""
        assert secrets.should_use_gsm() is False

    @patch.dict(os.environ, {"USE_GSM": "0"})
    def test_should_use_gsm_0(self):
        """Test 6: Retorna False cuando USE_GSM=0"""
        assert secrets.should_use_gsm() is False

    @patch.dict(os.environ, {"USE_GSM": "something_else"})
    def test_should_use_gsm_other_value(self):
        """Test 7: Retorna False para otros valores"""
        assert secrets.should_use_gsm() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_should_use_gsm_not_set(self):
        """Test 8: Retorna False cuando USE_GSM no está definido"""
        assert secrets.should_use_gsm() is False