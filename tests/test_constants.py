import pytest
from src.core.constants import Defaults, EnvVars, Supabase, OAuth, Validation


class TestEnvVars:
    """Tests para la clase EnvVars"""

    def test_supabase_url(self):
        """Test 1: SUPABASE_URL definido correctamente"""
        assert EnvVars.SUPABASE_URL == "SUPABASE_URL"

    def test_supabase_key(self):
        """Test 2: SUPABASE_KEY definido correctamente"""
        assert EnvVars.SUPABASE_KEY == "SUPABASE_KEY"

    def test_supabase_jwt_secret(self):
        """Test 3: SUPABASE_JWT_SECRET definido correctamente"""
        assert EnvVars.SUPABASE_JWT_SECRET == "SUPABASE_JWT_SECRET"

    def test_gcp_project_id(self):
        """Test 4: GCP_PROJECT_ID definido correctamente"""
        assert EnvVars.GCP_PROJECT_ID == "GCP_PROJECT_ID"

    def test_use_gsm(self):
        """Test 5: USE_GSM definido correctamente"""
        assert EnvVars.USE_GSM == "USE_GSM"


class TestDefaults:
    """Tests para la clase Defaults"""

    def test_app_name(self):
        """Test 1: APP_NAME correcto"""
        assert Defaults.APP_NAME == "Supabase Auth API"

    def test_app_version(self):
        """Test 2: APP_VERSION correcto"""
        assert Defaults.APP_VERSION == "0.1.0"

    def test_api_v1_str(self):
        """Test 3: API_V1_STR correcto"""
        assert Defaults.API_V1_STR == "/api/v1"

    def test_cors_origins(self):
        """Test 4: CORS_ORIGINS tiene valor por defecto"""
        assert Defaults.CORS_ORIGINS == ["*"]

    def test_log_level_default(self):
        """Test 5: LOG_LEVEL default es INFO"""
        assert Defaults.LOG_LEVEL == "INFO"

    def test_debug_default(self):
        """Test 6: DEBUG default es False"""
        assert Defaults.DEBUG is False

    def test_testing_default(self):
        """Test 7: TESTING default es False"""
        assert Defaults.TESTING is False

    def test_use_gsm_default(self):
        """Test 8: USE_GSM default es False"""
        assert Defaults.USE_GSM is False


class TestValidation:
    """Tests para la clase Validation"""

    def test_min_password_length(self):
        """Test 1: MIN_PASSWORD_LENGTH es 8"""
        assert Validation.MIN_PASSWORD_LENGTH == 8


class TestSupabaseConstants:
    """Tests para la clase Supabase"""

    def test_required_secrets(self):
        """Test 1: REQUIRED_SECRETS contiene las claves necesarias"""
        assert "SUPABASE_URL" in Supabase.REQUIRED_SECRETS
        assert "SUPABASE_KEY" in Supabase.REQUIRED_SECRETS
        assert "SUPABASE_JWT_SECRET" in Supabase.REQUIRED_SECRETS
        assert len(Supabase.REQUIRED_SECRETS) == 3

    def test_full_name_field(self):
        """Test 2: FULL_NAME_FIELD es 'full_name'"""
        assert Supabase.FULL_NAME_FIELD == "full_name"

    def test_secret_path_template(self):
        """Test 3: SECRET_PATH_TEMPLATE tiene el formato correcto"""
        assert "{project_id}" in Supabase.SECRET_PATH_TEMPLATE
        assert "{secret_name}" in Supabase.SECRET_PATH_TEMPLATE

    def test_secret_path_template_format(self):
        """Test 4: SECRET_PATH_TEMPLATE se formatea correctamente"""
        result = Supabase.SECRET_PATH_TEMPLATE.format(
            project_id="test-project",
            secret_name="test-secret"
        )
        assert result == "projects/test-project/secrets/test-secret/versions/latest"


class TestOAuthConstants:
    """Tests para la clase OAuth"""

    def test_google_provider(self):
        """Test 1: GOOGLE provider es 'google'"""
        assert OAuth.GOOGLE == "google"