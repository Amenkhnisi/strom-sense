from fastapi import APIRouter, UploadFile, File
from utils.models import OCRResponse
import shutil
import os
import requests

router = APIRouter(prefix="/upload-bill", tags=["Upload Bill"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=OCRResponse)
async def parse_bill(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

        response = requests.post(
            'http://localhost:8000/ocr/pdf',
            files={'file': open(file_path, 'rb')}
        )
        data = response.json()

    return data
