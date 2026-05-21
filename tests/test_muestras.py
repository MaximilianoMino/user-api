import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException


class TestMuestraModels:
    """Tests for Pydantic models"""

    def test_muestra_create_valid(self):
        """Test 1: MuestraCreate con datos válidos"""
        from src.models.muestra import MuestraCreate

        muestra = MuestraCreate(
            peso_muestra=500.0,
        )

        assert muestra.peso_muestra == 500.0
        assert muestra.unidad_peso == "g"
        assert muestra.contexto == "bolsas"

    def test_muestra_create_con_kg(self):
        """Test 2: MuestraCreate con unidad kg"""
        from src.models.muestra import MuestraCreate

        muestra = MuestraCreate(
            peso_muestra=1.5,
            unidad_peso="kg",
        )

        assert muestra.unidad_peso == "kg"

    def test_muestra_create_peso_negativo_error(self):
        """Test 3: peso_muestra negativo -> error"""
        from src.models.muestra import MuestraCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MuestraCreate(peso_muestra=-10.0)

    def test_muestra_create_peso_cero_error(self):
        """Test 4: peso_muestra cero -> error"""
        from src.models.muestra import MuestraCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MuestraCreate(peso_muestra=0)

    def test_muestra_create_unidad_invalida_error(self):
        """Test 5: unidad_peso inválida -> error"""
        from src.models.muestra import MuestraCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MuestraCreate(peso_muestra=100.0, unidad_peso="libras")

    def test_muestra_create_contexto_invalido_error(self):
        """Test 6: contexto inválido -> error"""
        from src.models.muestra import MuestraCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MuestraCreate(peso_muestra=100.0, contexto="cajas")

    def test_muestra_update_valid(self):
        """Test 7: MuestraUpdate con observaciones"""
        from src.models.muestra import MuestraUpdate

        update = MuestraUpdate(observaciones="Observación de prueba")

        assert update.observaciones == "Observación de prueba"

    def test_muestra_response_model(self):
        """Test 8: MuestraResponse fields"""
        from src.models.muestra import MuestraResponse
        from uuid import uuid4
        from datetime import datetime

        response = MuestraResponse(
            muestra_id=uuid4(),
            lote_id=uuid4(),
            contexto="bolsas",
            peso_muestra=500.0,
            unidad_peso="g",
            estado="tomada",
            observaciones=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert response.estado == "tomada"
        assert response.peso_muestra == 500.0


class TestMuestraService:
    """Tests for muestra service functions"""

    @pytest.mark.asyncio
    async def test_validate_lote_for_muestra_lote_not_found(self):
        """Test 9: Lote no encontrado -> error"""
        from src.services.muestra_service import validate_lote_for_muestra

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc:
            await validate_lote_for_muestra(mock_db, "lote-id", 1)

        assert str(exc.value) == "LOTE_NOT_FOUND"


class TestMuestraRepository:
    """Tests for MuestraRepository"""

    def test_to_dict(self):
        """Test 10: to_dict conversion"""
        from src.models.muestra import Muestra
        from uuid import uuid4

        mock_muestra = MagicMock()
        mock_muestra.muestra_id = uuid4()
        mock_muestra.lote_id = uuid4()
        mock_muestra.contexto = "bolsas"
        mock_muestra.peso_muestra = 500.0
        mock_muestra.unidad_peso = "g"
        mock_muestra.estado = "tomada"
        mock_muestra.observaciones = "test"
        mock_muestra.created_at = None
        mock_muestra.updated_at = None

        from src.repositories.muestra_repository import MuestraRepository

        repo = MuestraRepository(None)
        result = repo.to_dict(mock_muestra)

        assert result["contexto"] == "bolsas"
        assert result["peso_muestra"] == 500.0
        assert result["estado"] == "tomada"