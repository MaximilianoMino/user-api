import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestAnalisisModels:
    """Tests for Pydantic models"""

    def test_parametro_create_valid(self):
        """Test 1: ParametroCreate con datos válidos"""
        from src.models.analisis import ParametroCreate

        param = ParametroCreate(
            parametro_id=1,
            valor=14.5,
            comentario="Algo elevado"
        )

        assert param.parametro_id == 1
        assert param.valor == 14.5
        assert param.comentario == "Algo elevado"

    def test_parametro_create_sin_comentario(self):
        """Test 2: ParametroCreate sin comentario"""
        from src.models.analisis import ParametroCreate

        param = ParametroCreate(
            parametro_id=2,
            valor=1.2
        )

        assert param.comentario is None

    def test_parametro_create_valor_negativo_error(self):
        """Test 3: valor negativo -> error"""
        from src.models.analisis import ParametroCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ParametroCreate(parametro_id=1, valor=-5)

    def test_analisis_create_valid(self):
        """Test 4: AnalisisCreate con parámetros válidos"""
        from src.models.analisis import AnalisisCreate, ParametroCreate

        analisis = AnalisisCreate(
            parametros=[
                ParametroCreate(parametro_id=1, valor=14.5),
                ParametroCreate(parametro_id=2, valor=1.2),
            ]
        )

        assert len(analisis.parametros) == 2

    def test_analisis_create_sin_parametros_error(self):
        """Test 5: Sin parámetros -> error"""
        from src.models.analisis import AnalisisCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnalisisCreate(parametros=[])

    def test_analisis_update_valid(self):
        """Test 6: AnalisisUpdate con observaciones"""
        from src.models.analisis import AnalisisUpdate

        update = AnalisisUpdate(
            observaciones_generales="Análisis revisado por el laboratorio"
        )

        assert update.observaciones_generales == "Análisis revisado por el laboratorio"

    def test_analisis_update_sin_observaciones(self):
        """Test 7: AnalisisUpdate sin observaciones"""
        from src.models.analisis import AnalisisUpdate

        update = AnalisisUpdate()

        assert update.observaciones_generales is None


class TestAnalisisServiceValidation:
    """Tests for analysis service validation functions"""

    @pytest.mark.asyncio
    async def test_validate_muestra_not_found(self):
        """Test 8: Muestra no encontrada -> error"""
        from src.services.analisis_service import validate_muestra_for_analisis

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc:
            await validate_muestra_for_analisis(mock_db, str(uuid4()), 1)

        assert str(exc.value) == "MUESTRA_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validate_muestra_no_tomada(self):
        """Test 9: Muestra no está en estado 'tomada' -> error"""
        from src.services.analisis_service import validate_muestra_for_analisis
        from src.models.muestra import Muestra, MuestraEstado

        mock_muestra = MagicMock(spec=Muestra)
        mock_muestra.muestra_id = uuid4()
        mock_muestra.estado = MuestraEstado.INICIADA
        mock_muestra.peso_muestra = 1000.0

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_muestra.lote = mock_lote

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_muestra)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc:
            await validate_muestra_for_analisis(mock_db, str(uuid4()), 1)

        assert str(exc.value) == "MUESTRA_NO_TOMADA"


class TestAnalisisRepository:
    """Tests for AnalisisRepository"""

    @pytest.mark.asyncio
    async def test_has_analisis_for_muestra_true(self):
        """Test 10: Ya existe análisis -> True"""
        from src.repositories.analisis_repository import AnalisisRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=1)
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AnalisisRepository(mock_db)
        result = await repo.has_analisis_for_muestra(str(uuid4()))

        assert result is True

    @pytest.mark.asyncio
    async def test_has_analisis_for_muestra_false(self):
        """Test 11: No existe análisis -> False"""
        from src.repositories.analisis_repository import AnalisisRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=0)
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AnalisisRepository(mock_db)
        result = await repo.has_analisis_for_muestra(str(uuid4()))

        assert result is False

    @pytest.mark.asyncio
    async def test_get_parametro_by_id_not_found(self):
        """Test 12: Parámetro no encontrado"""
        from src.repositories.analisis_repository import AnalisisRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AnalisisRepository(mock_db)
        result = await repo.get_parametro_by_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_parametro_by_codigo_not_found(self):
        """Test 13: Parámetro por código no encontrado"""
        from src.repositories.analisis_repository import AnalisisRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AnalisisRepository(mock_db)
        result = await repo.get_parametro_by_codigo("producto_principal")

        assert result is None