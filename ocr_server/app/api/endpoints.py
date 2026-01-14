
from fastapi import APIRouter, HTTPException
from app.schemas import OCRRequest, OCRResponse
from app.core.ocr import OCREngine

router = APIRouter()

@router.post("/ocr", response_model=OCRResponse, summary="OCR Recognition")
async def ocr_endpoint(request: OCRRequest):
    """
    Perform OCR on the provided base64 image.
    Compatible with legacy OCR server.
    """
    engine = OCREngine.get_instance()
    try:
        data = await engine.predict(
            request.image_base64,
            target_text=request.target_text,
            max_side=request.max_side
        )
        return OCRResponse(code=0, data=data, msg="success")
    except Exception as e:
        # In case of error, return code -1 as per convention
        return OCRResponse(code=-1, data=None, msg=str(e))

@router.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}
