import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.dependencies import get_current_user
from src.core.database import get_db


class TestCatalogoModels:
    """Tests for Pydantic schemas in catalogo.py"""

    def test_variedad_response_valid(self):
        from src.models.catalogo import VariedadResponse

        v = VariedadResponse(variedad_id=1, codigo="ADZUKI")
        assert v.variedad_id == 1
        assert v.codigo == "ADZUKI"

    def test_subvariedad_response_valid(self):
        from src.models.catalogo import SubVariedadResponse

        sv = SubVariedadResponse(sub_variedad_id=2, codigo="CRIOLLO", variedad_id=1)
        assert sv.sub_variedad_id == 2
        assert sv.codigo == "CRIOLLO"
        assert sv.variedad_id == 1

    def test_temporada_response_valid(self):
        from src.models.catalogo import TemporadaResponse

        t = TemporadaResponse(temporada_id=1, codigo="2025")
        assert t.temporada_id == 1
        assert t.codigo == "2025"

    def test_variedad_response_from_attributes(self):
        from src.models.catalogo import VariedadResponse

        mock_obj = MagicMock()
        mock_obj.variedad_id = 13
        mock_obj.codigo = "CRIOLLO"

        v = VariedadResponse.model_validate(mock_obj)
        assert v.variedad_id == 13
        assert v.codigo == "CRIOLLO"


class TestCatalogosEndpoints:
    """Tests for catalogos endpoints"""

    @pytest.mark.asyncio
    async def test_listar_variedades_success(self):
        from src.api.endpoints.catalogos import listar_variedades
        from src.models.variedad import Variedad

        mock_var1 = MagicMock(spec=Variedad)
        mock_var1.variedad_id = 1
        mock_var1.codigo = "ADZUKI"

        mock_var2 = MagicMock(spec=Variedad)
        mock_var2.variedad_id = 13
        mock_var2.codigo = "CRIOLLO"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_var1, mock_var2]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await listar_variedades(db=mock_db, current_user={"user_id": 1})

        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["variedad_id"] == 1
        assert result["data"][1]["codigo"] == "CRIOLLO"

    @pytest.mark.asyncio
    async def test_listar_subvariedades_sin_filtro(self):
        from src.api.endpoints.catalogos import listar_subvariedades
        from src.models.sub_variedad import SubVariedad

        mock_sv1 = MagicMock(spec=SubVariedad)
        mock_sv1.sub_variedad_id = 1
        mock_sv1.codigo = "A"
        mock_sv1.variedad_id = 1

        mock_sv2 = MagicMock(spec=SubVariedad)
        mock_sv2.sub_variedad_id = 2
        mock_sv2.codigo = "B"
        mock_sv2.variedad_id = 14

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_sv1, mock_sv2]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await listar_subvariedades(variedad_id=None, db=mock_db, current_user={"user_id": 1})

        assert "data" in result
        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_listar_subvariedades_con_filtro(self):
        from src.api.endpoints.catalogos import listar_subvariedades
        from src.models.sub_variedad import SubVariedad

        mock_sv = MagicMock(spec=SubVariedad)
        mock_sv.sub_variedad_id = 3
        mock_sv.codigo = "X"
        mock_sv.variedad_id = 1

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_sv]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await listar_subvariedades(variedad_id=1, db=mock_db, current_user={"user_id": 1})

        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["variedad_id"] == 1

    @pytest.mark.asyncio
    async def test_listar_temporadas_success(self):
        from src.api.endpoints.catalogos import listar_temporadas
        from src.models.temporada import Temporada

        mock_t1 = MagicMock(spec=Temporada)
        mock_t1.temporada_id = 1
        mock_t1.codigo = "2025"

        mock_t2 = MagicMock(spec=Temporada)
        mock_t2.temporada_id = 2
        mock_t2.codigo = "2026"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_t1, mock_t2]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await listar_temporadas(db=mock_db, current_user={"user_id": 1})

        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["temporada_id"] == 1
        assert result["data"][1]["codigo"] == "2026"
