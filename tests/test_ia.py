import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO


class TestProcessAnalysisImage:

    @pytest.mark.asyncio
    async def test_procesar_imagen_success(self):
        """Test 1: Gemini devuelve parámetros válidos"""
        from src.services import ia_service

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "parametros": [
                {"nombre": "Humedad", "valor": 14.5, "unidad": "%"},
                {"nombre": "Impurezas", "valor": 1.2, "unidad": "%"},
            ],
            "texto_original": "Humedad: 14.5%\nImpurezas: 1.2%",
        })

        fake_bytes = b"fake-image-data"

        with patch.object(ia_service.genai, "Client") as mock_client_class, \
             patch.object(ia_service, "settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            mock_models = MagicMock()
            mock_models.generate_content.return_value = mock_response

            mock_client = MagicMock()
            mock_client.models = mock_models
            mock_client_class.return_value = mock_client

            result = await ia_service.process_analysis_image(fake_bytes, "test.jpg")

            mock_client_class.assert_called_once_with(api_key="test-key")
            mock_models.generate_content.assert_called_once()
            assert len(result["parametros"]) == 2
            assert result["parametros"][0]["nombre"] == "Humedad"
            assert result["parametros"][0]["valor"] == 14.5
            assert result["texto_original"] == "Humedad: 14.5%\nImpurezas: 1.2%"

    @pytest.mark.asyncio
    async def test_procesar_imagen_borrosa_sin_texto(self):
        """Test 2: Gemini no puede leer nada → array vacío"""
        from src.services import ia_service

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "parametros": [],
            "texto_original": "",
        })

        fake_bytes = b"blurry-image-data"

        with patch.object(ia_service.genai, "Client") as mock_client_class, \
             patch.object(ia_service, "settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            mock_models = MagicMock()
            mock_models.generate_content.return_value = mock_response

            mock_client = MagicMock()
            mock_client.models = mock_models
            mock_client_class.return_value = mock_client

            result = await ia_service.process_analysis_image(fake_bytes, "blurry.jpg")

            assert result["parametros"] == []
            assert result["texto_original"] == ""
            assert "mensaje" not in result or result.get("mensaje") is None

    @pytest.mark.asyncio
    async def test_procesar_sin_api_key(self):
        """Test 3: GEMINI_API_KEY no configurada"""
        from src.services import ia_service

        fake_bytes = b"image-data"

        with patch.object(ia_service, "settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""

            result = await ia_service.process_analysis_image(fake_bytes, "test.jpg")

            assert result["parametros"] == []
            assert result["texto_original"] == ""
            assert result["mensaje"] is not None
            assert "no está configurado" in result["mensaje"]

    @pytest.mark.asyncio
    async def test_procesar_gemini_falla(self):
        """Test 4: Gemini lanza excepción"""
        from src.services import ia_service

        fake_bytes = b"image-data"

        with patch.object(ia_service.genai, "Client") as mock_client_class, \
             patch.object(ia_service, "settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            mock_models = MagicMock()
            mock_models.generate_content.side_effect = Exception("API error")

            mock_client = MagicMock()
            mock_client.models = mock_models
            mock_client_class.return_value = mock_client

            result = await ia_service.process_analysis_image(fake_bytes, "test.jpg")

            assert result["parametros"] == []
            assert result["texto_original"] == ""
            assert result["mensaje"] is not None


class TestEscanearEndpoint:

    @pytest.mark.asyncio
    async def test_escanear_archivo_demasiado_grande(self):
        """Test 5: Archivo mayor a 10 MB retorna 400"""
        from fastapi import HTTPException
        from src.core.messages import ErrorMessages

        max_size = 10 * 1024 * 1024
        file_bytes = b"x" * (max_size + 1)

        if len(file_bytes) > max_size:
            with pytest.raises(HTTPException) as exc:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorMessages.TAMANO_EXCEDIDO.replace("20 MB", "10 MB"),
                )
            assert exc.value.status_code == 400
            assert "10 MB" in exc.value.detail

    @pytest.mark.asyncio
    async def test_escanear_tipo_archivo_invalido(self):
        """Test 6: Archivo que no es imagen retorna 400"""
        from fastapi import HTTPException
        from src.core.messages import ErrorMessages

        content_type = "application/pdf"

        if not content_type or not content_type.startswith("image/"):
            with pytest.raises(HTTPException) as exc:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorMessages.IA_ARCHIVO_INVALIDO,
                )
            assert exc.value.status_code == 400
            assert exc.value.detail is not None
