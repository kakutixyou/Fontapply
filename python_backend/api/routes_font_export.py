from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from python_backend.schemas.font_export_schema import (
    FontExportFormat,
    FontExportRequest,
    FontExportValidateResponse,
    ValidationErrorDetail,
)

router = APIRouter(prefix="/fonts", tags=["font-export"])

@router.post("/export")
async def export_font(req: FontExportRequest) -> Response:
    """
    フォントのエクスポート機能。
    現在は新しいアーキテクチャ（大動脈）への移行中のため、一時的に501を返します。
    新しい FontAssembler が完成次第、ここを繋ぎ直します。
    """
    raise HTTPException(
        status_code=501, 
        detail="Font export engine is currently being upgraded to support the new JSON architecture."
    )

@router.post("/export/validate", response_model=FontExportValidateResponse)
async def validate_export_font(req: FontExportRequest) -> FontExportValidateResponse:
    """
    エクスポート前のバリデーション機能。
    現在は常に成功を返すモックとして機能します。
    """
    return FontExportValidateResponse(ok=True)