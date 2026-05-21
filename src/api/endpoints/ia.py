import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.api.dependencies import get_current_user, get_org_id
from src.core.messages import ErrorMessages
from src.models.ia import IAResponse
from src.services import ia_service

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/ia/escanear",
    response_model=IAResponse,
    status_code=status.HTTP_200_OK,
)
async def escanear_imagen(
    file: UploadFile,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
) -> IAResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=ErrorMessages.IA_ARCHIVO_INVALIDO,
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=ErrorMessages.TAMANO_EXCEDIDO.replace("20 MB", "10 MB"),
        )

    result = await ia_service.process_analysis_image(file_bytes, file.filename or "unknown")

    return IAResponse(
        parametros=result.get("parametros", []),
        texto_original=result.get("texto_original", ""),
        mensaje=result.get("mensaje"),
    )
