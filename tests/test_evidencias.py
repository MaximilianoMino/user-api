import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestGenerateUploadUrl:
    """Tests for generate_upload_url service function"""

    @pytest.mark.asyncio
    async def test_generate_upload_url_success(self):
        """Test 1: Generate upload URL with valid data"""
        from src.services.evidencia_service import generate_upload_url

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()

        mock_bucket.create_signed_upload_url.return_value = {
            "url": "https://example.com/upload/signed-url",
            "path": "lotes/test-lote/evidencias/test.jpg",
        }
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage

        result = await generate_upload_url(
            lote_id="test-lote-id",
            tipo="foto",
            content_type="image/jpeg",
            supabase_client=mock_supabase,
        )

        assert "data" in result
        assert "upload_url" in result["data"]
        assert "file_key" in result["data"]
        assert result["data"]["file_key"].startswith("lotes/test-lote-id/evidencias/")
        assert result["data"]["file_key"].endswith(".jpg")
        mock_bucket.create_signed_upload_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_upload_url_invalid_type(self):
        """Test 2: Generate upload URL with invalid type"""
        from src.services.evidencia_service import generate_upload_url

        mock_supabase = MagicMock()

        with pytest.raises(ValueError) as exc:
            await generate_upload_url(
                lote_id="test-lote-id",
                tipo="documento",
                content_type="application/pdf",
                supabase_client=mock_supabase,
            )

        assert str(exc.value) == "TIPO_INVALIDO"


class TestConfirmUpload:
    """Tests for confirm_upload service function"""

    @pytest.mark.asyncio
    async def test_confirm_upload_success(self):
        """Test 3: Confirm upload and create evidencia record"""
        from src.services.evidencia_service import confirm_upload

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()
        mock_supabase = MagicMock()

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_evidencia = MagicMock()
        mock_evidencia.evidencia_id = uuid4()
        mock_evidencia.url = "https://example.com/public/url"
        mock_evidencia.tipo = "foto"
        mock_evidencia.estado = "activa"
        mock_repo.create = AsyncMock(return_value=mock_evidencia)
        mock_repo.to_response_dict = MagicMock(return_value={
            "evidencia_id": str(mock_evidencia.evidencia_id),
            "url": mock_evidencia.url,
            "tipo": mock_evidencia.tipo,
            "estado": mock_evidencia.estado,
        })

        mock_supabase.storage.from_().get_public_url.return_value = {
            "publicUrl": "https://example.com/public/url"
        }

        result = await confirm_upload(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            lote_id=str(uuid4()),
            file_key="lotes/test-lote-id/evidencias/test.jpg",
            tipo="foto",
            muestra_id=None,
            user_id=1,
            org_id=1,
            supabase_client=mock_supabase,
        )

        assert "data" in result
        assert result["data"]["tipo"] == "foto"
        assert result["data"]["estado"] == "activa"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_upload_invalid_type(self):
        """Test 4: Confirm upload with invalid type"""
        from src.services.evidencia_service import confirm_upload

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()
        mock_supabase = MagicMock()

        with pytest.raises(ValueError) as exc:
            await confirm_upload(
                repo=mock_repo,
                db=mock_db,
                lote_repo=mock_lote_repo,
                lote_id="test-lote-id",
                file_key="lotes/test-lote-id/evidencias/test.jpg",
                tipo="documento",
                muestra_id=None,
                user_id=1,
                org_id=1,
                supabase_client=mock_supabase,
            )

        assert str(exc.value) == "TIPO_INVALIDO"


class TestListEvidencias:
    """Tests for list_evidencias service function"""

    @pytest.mark.asyncio
    async def test_list_evidencias_empty(self):
        """Test 5: List evidencias for lote with no evidencias"""
        from src.services.evidencia_service import list_evidencias

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_repo.list_by_lote = AsyncMock(return_value=[])

        result = await list_evidencias(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            lote_id=str(uuid4()),
            org_id=1,
        )

        assert "data" in result
        assert result["data"] == []

    @pytest.mark.asyncio
    async def test_list_evidencias_with_data(self):
        """Test 6: List evidencias for lote with existing evidencias"""
        from src.services.evidencia_service import list_evidencias

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_evidencia_1 = MagicMock()
        mock_evidencia_1.evidencia_id = uuid4()
        mock_evidencia_1.url = "https://example.com/photo1.jpg"
        mock_evidencia_1.tipo = "foto"
        mock_evidencia_1.created_at = MagicMock()
        mock_evidencia_1.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_evidencia_2 = MagicMock()
        mock_evidencia_2.evidencia_id = uuid4()
        mock_evidencia_2.url = "https://example.com/video1.mp4"
        mock_evidencia_2.tipo = "video"
        mock_evidencia_2.created_at = MagicMock()
        mock_evidencia_2.created_at.isoformat.return_value = "2024-01-02T00:00:00"

        mock_repo.list_by_lote = AsyncMock(return_value=[mock_evidencia_1, mock_evidencia_2])
        mock_repo.to_list_item_dict = MagicMock(side_effect=[
            {
                "evidencia_id": str(mock_evidencia_1.evidencia_id),
                "url": mock_evidencia_1.url,
                "tipo": mock_evidencia_1.tipo,
                "created_at": "2024-01-01T00:00:00",
            },
            {
                "evidencia_id": str(mock_evidencia_2.evidencia_id),
                "url": mock_evidencia_2.url,
                "tipo": mock_evidencia_2.tipo,
                "created_at": "2024-01-02T00:00:00",
            },
        ])

        result = await list_evidencias(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            lote_id=str(uuid4()),
            org_id=1,
        )

        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["tipo"] == "foto"
        assert result["data"][1]["tipo"] == "video"


class TestDeleteEvidencia:
    """Tests for delete_evidencia service function"""

    @pytest.mark.asyncio
    async def test_delete_evidencia_success(self):
        """Test 7: Soft delete evidencia successfully"""
        from src.services.evidencia_service import delete_evidencia

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()
        mock_supabase = MagicMock()

        evidencia_id = uuid4()
        mock_evidencia = MagicMock()
        mock_evidencia.evidencia_id = evidencia_id
        mock_evidencia.lote_id = uuid4()
        mock_repo.get_by_id = AsyncMock(return_value=mock_evidencia)

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_deleted = MagicMock()
        mock_deleted.estado = "eliminada"
        mock_repo.soft_delete = AsyncMock(return_value=mock_deleted)

        result = await delete_evidencia(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            evidencia_id=str(evidencia_id),
            user_id=1,
            org_id=1,
            supabase_client=mock_supabase,
        )

        assert result["message"] == "Evidencia eliminada correctamente"
        mock_repo.soft_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_evidencia_not_found(self):
        """Test 8: Delete evidencia that doesn't exist"""
        from src.services.evidencia_service import delete_evidencia

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()
        mock_supabase = MagicMock()

        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc:
            await delete_evidencia(
                repo=mock_repo,
                db=mock_db,
                lote_repo=mock_lote_repo,
                evidencia_id=str(uuid4()),
                user_id=1,
                org_id=1,
                supabase_client=mock_supabase,
            )

        assert str(exc.value) == "EVIDENCIA_NOT_FOUND"
