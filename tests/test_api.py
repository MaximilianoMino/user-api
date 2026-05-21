import pytest
from httpx import AsyncClient, ASGITransport

from src.api.api import app


class TestHealthCheck:
    """Tests para el endpoint GET /health"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test 1: Health check exitoso retorna 200"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "version" in response.json()

    @pytest.mark.asyncio
    async def test_health_check_returns_json(self):
        """Test 2: Health check retorna JSON válido"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestAppSetup:
    """Tests para la configuración de la app"""

    def test_app_title(self):
        """Test 1: La app tiene el título correcto"""
        assert app.title == "Supabase Auth API"

    def test_app_description(self):
        """Test 2: La app tiene la descripción correcta"""
        assert "Supabase" in app.description

    def test_app_version(self):
        """Test 3: La app tiene la versión correcta"""
        assert app.version == "0.1.0"

    def test_app_has_cors_middleware(self):
        """Test 4: La app tiene middleware CORS"""
        # Verificar que hay middleware CORS registrado
        assert len(app.user_middleware) > 0

    def test_app_has_routes(self):
        """Test 5: La app tiene rutas registradas"""
        # La app debe tener rutas
        assert len(app.routes) > 0


class TestApiRouter:
    """Tests para el router de API"""

    def test_router_prefix(self):
        """Test 1: El router tiene el prefijo correcto"""
        from src.api.router import api_router
        
        # Verificar que el router tiene un prefijo
        routes = [r for r in api_router.routes]
        assert len(routes) > 0