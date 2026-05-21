import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestGenerateUploadUrl:
    """Tests for generate_upload_url service function"""

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_pdf(self):
        """Test 1: Generate upload URL with valid PDF"""
        from src.services.documento_service import generate_upload_url

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()

        mock_bucket.create_signed_upload_url.return_value = {
            "url": "https://example.com/upload/signed-url",
            "path": "lotes/test-lote/documentos/test.pdf",
        }
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage

        result = await generate_upload_url(
            lote_id="test-lote-id",
            nombre_original="test.pdf",
            tipo_mime="application/pdf",
            tamano_bytes=1_000_000,
            supabase_client=mock_supabase,
        )

        assert "data" in result
        assert "upload_url" in result["data"]
        assert "file_key" in result["data"]
        assert result["data"]["file_key"].startswith("lotes/test-lote-id/documentos/")
        assert result["data"]["file_key"].endswith(".pdf")
        mock_bucket.create_signed_upload_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_image(self):
        """Test 2: Generate upload URL with valid image"""
        from src.services.documento_service import generate_upload_url

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()

        mock_bucket.create_signed_upload_url.return_value = {
            "url": "https://example.com/upload/signed-url",
            "path": "lotes/test-lote/documentos/test.jpg",
        }
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage

        result = await generate_upload_url(
            lote_id="test-lote-id",
            nombre_original="test.png",
            tipo_mime="image/png",
            tamano_bytes=500_000,
            supabase_client=mock_supabase,
        )

        assert "data" in result
        assert result["data"]["file_key"].endswith(".png")

    @pytest.mark.asyncio
    async def test_generate_upload_url_invalid_content_type(self):
        """Test 3: Generate upload URL with invalid content type"""
        from src.services.documento_service import generate_upload_url

        mock_supabase = MagicMock()

        with pytest.raises(ValueError) as exc:
            await generate_upload_url(
                lote_id="test-lote-id",
                nombre_original="test.exe",
                tipo_mime="application/x-executable",
                tamano_bytes=1_000_000,
                supabase_client=mock_supabase,
            )

        assert str(exc.value) == "CONTENT_TYPE_INVALIDO"

    @pytest.mark.asyncio
    async def test_generate_upload_url_size_exceeded(self):
        """Test 4: Generate upload URL with size exceeding limit"""
        from src.services.documento_service import generate_upload_url
        from src.models.documento import TIPO_MAX_SIZE_BYTES

        mock_supabase = MagicMock()

        with pytest.raises(ValueError) as exc:
            await generate_upload_url(
                lote_id="test-lote-id",
                nombre_original="large.pdf",
                tipo_mime="application/pdf",
                tamano_bytes=TIPO_MAX_SIZE_BYTES + 1,
                supabase_client=mock_supabase,
            )

        assert str(exc.value) == "TAMANO_EXCEDIDO"


class TestConfirmUpload:
    """Tests for confirm_upload service function"""

    @pytest.mark.asyncio
    async def test_confirm_upload_success(self):
        """Test 5: Confirm upload and create documento record"""
        from src.services.documento_service import confirm_upload

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()
        mock_supabase = MagicMock()

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_documento = MagicMock()
        mock_documento.lote_documento_id = uuid4()
        mock_documento.url = "https://example.com/public/url"
        mock_documento.nombre_original = "test.pdf"
        mock_documento.nombre_archivo = "test.pdf"
        mock_documento.tipo_mime = "application/pdf"
        mock_documento.extension = "pdf"
        mock_documento.tamano_bytes = 1_000_000
        mock_documento.estado = "activo"
        mock_repo.create = AsyncMock(return_value=mock_documento)
        mock_repo.to_response_dict = MagicMock(return_value={
            "lote_documento_id": str(mock_documento.lote_documento_id),
            "url": mock_documento.url,
            "nombre_original": mock_documento.nombre_original,
            "estado": mock_documento.estado,
        })

        mock_supabase.storage.from_().get_public_url.return_value = {
            "publicUrl": "https://example.com/public/url"
        }

        result = await confirm_upload(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            lote_id=str(uuid4()),
            file_key="lotes/test-lote-id/documentos/test.pdf",
            nombre_original="test.pdf",
            tipo_mime="application/pdf",
            tamano_bytes=1_000_000,
            user_id=1,
            org_id=1,
            supabase_client=mock_supabase,
        )

        assert "data" in result
        assert result["data"]["estado"] == "activo"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_upload_lote_not_found(self):
        """Test 6: Confirm upload when lote doesn't exist"""
        from src.services.documento_service import confirm_upload

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()
        mock_supabase = MagicMock()

        mock_lote_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc:
            await confirm_upload(
                repo=mock_repo,
                db=mock_db,
                lote_repo=mock_lote_repo,
                lote_id=str(uuid4()),
                file_key="lotes/test-lote-id/documentos/test.pdf",
                nombre_original="test.pdf",
                tipo_mime="application/pdf",
                tamano_bytes=1_000_000,
                user_id=1,
                org_id=1,
                supabase_client=mock_supabase,
            )

        assert str(exc.value) == "LOTE_NOT_FOUND"


class TestListDocumentos:
    """Tests for list_documentos service function"""

    @pytest.mark.asyncio
    async def test_list_documentos_empty(self):
        """Test 7: List documentos for lote with no documentos"""
        from src.services.documento_service import list_documentos

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_repo.list_by_lote = AsyncMock(return_value=[])

        result = await list_documentos(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            lote_id=str(uuid4()),
            org_id=1,
        )

        assert "data" in result
        assert result["data"] == []

    @pytest.mark.asyncio
    async def test_list_documentos_with_data(self):
        """Test 8: List documentos for lote with existing documentos"""
        from src.services.documento_service import list_documentos

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_doc_1 = MagicMock()
        mock_doc_1.lote_documento_id = uuid4()
        mock_doc_1.url = "https://example.com/doc1.pdf"
        mock_doc_1.nombre_original = "doc1.pdf"
        mock_doc_1.tipo_mime = "application/pdf"
        mock_doc_1.tamano_bytes = 1_000_000
        mock_doc_1.categoria = "certificado"
        mock_doc_1.created_at = MagicMock()
        mock_doc_1.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_doc_2 = MagicMock()
        mock_doc_2.lote_documento_id = uuid4()
        mock_doc_2.url = "https://example.com/doc2.xlsx"
        mock_doc_2.nombre_original = "doc2.xlsx"
        mock_doc_2.tipo_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        mock_doc_2.tamano_bytes = 2_000_000
        mock_doc_2.categoria = None
        mock_doc_2.created_at = MagicMock()
        mock_doc_2.created_at.isoformat.return_value = "2024-01-02T00:00:00"

        mock_repo.list_by_lote = AsyncMock(return_value=[mock_doc_1, mock_doc_2])
        mock_repo.to_list_item_dict = MagicMock(side_effect=[
            {
                "lote_documento_id": str(mock_doc_1.lote_documento_id),
                "url": mock_doc_1.url,
                "nombre_original": mock_doc_1.nombre_original,
                "tipo_mime": mock_doc_1.tipo_mime,
                "tamano_bytes": mock_doc_1.tamano_bytes,
                "categoria": mock_doc_1.categoria,
                "created_at": "2024-01-01T00:00:00",
            },
            {
                "lote_documento_id": str(mock_doc_2.lote_documento_id),
                "url": mock_doc_2.url,
                "nombre_original": mock_doc_2.nombre_original,
                "tipo_mime": mock_doc_2.tipo_mime,
                "tamano_bytes": mock_doc_2.tamano_bytes,
                "categoria": mock_doc_2.categoria,
                "created_at": "2024-01-02T00:00:00",
            },
        ])

        result = await list_documentos(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            lote_id=str(uuid4()),
            org_id=1,
        )

        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["nombre_original"] == "doc1.pdf"
        assert result["data"][1]["nombre_original"] == "doc2.xlsx"


class TestDeleteDocumento:
    """Tests for delete_documento service function"""

    @pytest.mark.asyncio
    async def test_delete_documento_success(self):
        """Test 9: Soft delete documento successfully"""
        from src.services.documento_service import delete_documento

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()

        documento_id = uuid4()
        mock_documento = MagicMock()
        mock_documento.lote_documento_id = documento_id
        mock_documento.lote_id = uuid4()
        mock_repo.get_by_id = AsyncMock(return_value=mock_documento)

        mock_lote = MagicMock()
        mock_lote.org_id = 1
        mock_lote_repo.get_by_id = AsyncMock(return_value=mock_lote)

        mock_deleted = MagicMock()
        mock_deleted.estado = "eliminado"
        mock_repo.soft_delete = AsyncMock(return_value=mock_deleted)

        result = await delete_documento(
            repo=mock_repo,
            db=mock_db,
            lote_repo=mock_lote_repo,
            documento_id=str(documento_id),
            user_id=1,
            org_id=1,
        )

        assert result["message"] == "Documento eliminado correctamente"
        mock_repo.soft_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_documento_not_found(self):
        """Test 10: Delete documento that doesn't exist"""
        from src.services.documento_service import delete_documento

        mock_repo = AsyncMock()
        mock_db = AsyncMock()
        mock_lote_repo = AsyncMock()

        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc:
            await delete_documento(
                repo=mock_repo,
                db=mock_db,
                lote_repo=mock_lote_repo,
                documento_id=str(uuid4()),
                user_id=1,
                org_id=1,
            )

        assert str(exc.value) == "DOCUMENTO_NOT_FOUND"
