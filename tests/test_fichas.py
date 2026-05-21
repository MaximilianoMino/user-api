import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


class TestFichasModels:
    """Tests for Pydantic models"""

    def test_ficha_response_model(self):
        """Test 1: FichaResponse con datos válidos"""
        from src.models.ficha import FichaResponse
        from datetime import datetime

        ficha = FichaResponse(
            ficha_id=uuid4(),
            lote_id=uuid4(),
            link_token="test-token-123",
            link_publico="https://agryflow.app/ficha/test-token-123",
            estado="activa",
            version=1,
            created_at=datetime.utcnow()
        )

        assert ficha.estado == "activa"
        assert ficha.version == 1
        assert ficha.link_token == "test-token-123"

    def test_ficha_generate_response(self):
        """Test 2: FichaGenerateResponse wrapper"""
        from src.models.ficha import FichaGenerateResponse, FichaResponse
        from datetime import datetime

        ficha = FichaResponse(
            ficha_id=uuid4(),
            lote_id=uuid4(),
            link_token="test-token",
            estado="activa",
            version=1,
            created_at=datetime.utcnow()
        )

        response = FichaGenerateResponse(data=ficha)
        assert response.data.estado == "activa"

    def test_ficha_public_response(self):
        """Test 3: FichaPublicResponse con datos completos"""
        from src.models.ficha import (
            FichaPublicResponse, LotePublicResponse, OrganizacionPublicResponse,
            MuestraPublicResponse, AnalisisPublicResponse, EvidenciaPublicResponse,
            TrazabilidadResponse, ParametroAnalisisResponse
        )

        analisis = AnalisisPublicResponse(
            parametros=[
                ParametroAnalisisResponse(nombre="Humedad", valor=14.5, unidad="%")
            ],
            subtotal_danos=5.0,
            producto_principal=958.5,
            total_analizado=1000.0
        )

        response = FichaPublicResponse(
            lote=LotePublicResponse(lote_id=uuid4()),
            organizacion=OrganizacionPublicResponse(nombre="Test Org", tipo="productor"),
            muestra=MuestraPublicResponse(peso_muestra=1000.0, unidad_peso="g", contexto="bolsas"),
            analisis=analisis,
            evidencias=[],
            trazabilidad=TrazabilidadResponse()
        )

        assert response.organizacion.nombre == "Test Org"
        assert response.analisis.total_analizado == 1000.0


class TestFichasServiceValidation:
    """Tests for fichas service validation"""

    @pytest.mark.asyncio
    async def test_validar_requisitos_lote_not_found(self):
        """Test 4: Lote no encontrado -> error"""
        from src.services.ficha_service import validar_requisitos_lote

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc:
            await validar_requisitos_lote(mock_db, str(uuid4()), 1)

        assert str(exc.value) == "LOTE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validar_requisitos_lote_wrong_org(self):
        """Test 5: Lote de otra organización -> error"""
        from src.services.ficha_service import validar_requisitos_lote
        from src.models.lote import Lote

        mock_lote = MagicMock(spec=Lote)
        mock_lote.lote_id = uuid4()
        mock_lote.org_id = 999
        mock_lote.status = "analisis_completp"
        mock_lote.deleted_at = None

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_lote)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc:
            await validar_requisitos_lote(mock_db, str(uuid4()), 1)

        assert str(exc.value) == "LOTE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validar_requisitos_lote_no_analisis_completo(self):
        """Test 6: Lote sin análisis completo -> error"""
        from src.services.ficha_service import validar_requisitos_lote
        from src.models.lote import Lote

        mock_lote = MagicMock(spec=Lote)
        mock_lote.lote_id = uuid4()
        mock_lote.org_id = 1
        mock_lote.status = "borrador"
        mock_lote.deleted_at = None

        mock_db = AsyncMock()
        mock_result_lote = MagicMock()
        mock_result_lote.scalar_one_or_none = MagicMock(return_value=mock_lote)
        mock_db.execute = AsyncMock(return_value=mock_result_lote)

        with pytest.raises(ValueError) as exc:
            await validar_requisitos_lote(mock_db, str(uuid4()), 1)

        assert str(exc.value) == "REQUISITOS_INCOMPLETOS"


class TestFichasRepository:
    """Tests for FichaRepository"""

    @pytest.mark.asyncio
    async def test_get_ficha_activa_por_lote_not_found(self):
        """Test 7: Ficha activa no encontrada"""
        from src.repositories.ficha_repository import FichaRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = FichaRepository(mock_db)
        result = await repo.get_ficha_activa_por_lote(str(uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_por_token_not_found(self):
        """Test 8: Token no encontrado"""
        from src.repositories.ficha_repository import FichaRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = FichaRepository(mock_db)
        result = await repo.get_por_token("invalid-token")

        assert result is None

    def test_to_response_dict(self):
        """Test 9: to_response_dict conversion"""
        from src.repositories.ficha_repository import FichaRepository
        from src.models.otros import FichaReporte
        from datetime import datetime

        mock_ficha = MagicMock(spec=FichaReporte)
        mock_ficha.ficha_id = uuid4()
        mock_ficha.lote_id = uuid4()
        mock_ficha.link_token = "test-token-123"
        mock_ficha.estado = "activa"
        mock_ficha.version = 1
        mock_ficha.created_at = datetime.utcnow()
        mock_ficha.muestra_id = uuid4()

        repo = FichaRepository(None)
        result = repo.to_response_dict(mock_ficha, "https://example.com/ficha/test")

        assert result["link_token"] == "test-token-123"
        assert result["estado"] == "activa"
        assert result["link_publico"] == "https://example.com/ficha/test"

    def test_to_response_dict_without_link(self):
        """Test 10: to_response_dict sin link_publico"""
        from src.repositories.ficha_repository import FichaRepository
        from src.models.otros import FichaReporte
        from datetime import datetime

        mock_ficha = MagicMock(spec=FichaReporte)
        mock_ficha.ficha_id = uuid4()
        mock_ficha.lote_id = uuid4()
        mock_ficha.link_token = "test-token"
        mock_ficha.estado = "revocada"
        mock_ficha.version = 1
        mock_ficha.created_at = datetime.utcnow()
        mock_ficha.muestra_id = None

        repo = FichaRepository(None)
        result = repo.to_response_dict(mock_ficha)

        assert result["estado"] == "revocada"
        assert result["link_publico"] is None
        assert result["muestra_id"] is None