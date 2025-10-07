from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import os
import shutil
import requests
from utils.models import OCRResponse

router = APIRouter(prefix="/upload-bill", tags=["Upload Bill"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


EXTENSION_ROUTE_MAP: Dict[str, str] = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".txt": "text"
}


@router.post("/", response_model=OCRResponse)
async def parse_bill(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Determine route based on file extension
    ext = os.path.splitext(file.filename)[1].lower()
    route = EXTENSION_ROUTE_MAP.get(ext)

    if not route:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {ext}")

    # Forward to appropriate OCR route
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                f"http://localhost:8000/ocr/{route}",
                files={"file": f}
            )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"OCR processing failed: {str(e)}")

    return data
