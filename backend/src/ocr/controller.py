from fastapi import APIRouter, Depends, APIRouter,  UploadFile, File, HTTPException, Body, Request
from sqlalchemy.orm import Session
from .models import ParsedInvoiceData, ParseTextRequest
from .service import save_invoice_to_db
from src.database.core import get_db
from .models import OCRResponse
from datetime import datetime
from src.ocr.utils.Tesseract_config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_PDF_EXTENSION
from src.ocr.utils.utility_functions import validate_file_extension, validate_file_size, to_parsed_invoice_model
from src.ocr.utils.ocr import extract_text_from_image, extract_text_from_pdf
from src.ocr.utils.parser_patterns import parse_invoice_text, detect_supplier
import os
import uuid
import shutil
from typing import Dict
import logging
from src.rate_limiter import limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


UPLOAD_DIR = "uploads"
EXTENSION_ROUTE_MAP: Dict[str, str] = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".txt": "text"
}
# Save bill data


@router.post("/save-invoice")
def save_invoice(data: ParsedInvoiceData, db: Session = Depends(get_db)):
    invoice = save_invoice_to_db(data, db)
    return {"message": "Invoice saved", "id": invoice.id}

# OCR


@router.post("/upload-bill", response_model=OCRResponse,)
@limiter.limit("5/hour")
async def parse_bill(request: Request,
                     file: UploadFile = File(..., description="file to process"), preprocess: bool = True
                     ):
    """
    Extract text from file and parse energy bill data

    Args:
        file: file upload (JPG, pdf, BMP, png ,jpeg)
        preprocess: Whether to preprocess image (default: True)

    Returns:
        OCRResponse with parsed invoice data
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()

    logger.info(f"[{request_id}] Received file OCR request: {file.filename}")

    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Determine file type based on file extension
    ext = os.path.splitext(file.filename)[1].lower()
    file_type = EXTENSION_ROUTE_MAP.get(ext)

    if not file_type:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {ext}")

    # Forward to appropriate OCR route

    try:
        # Read file and validate size

        # Extract text
        logger.info(f"[{request_id}] Starting OCR processing")

        if file_type == "image":
            logger.info(
                f"[{request_id}] Received image OCR request: {file.filename}")
            # Validate file extension
            validate_file_extension(file.filename, ALLOWED_IMAGE_EXTENSIONS)
            await file.seek(0)
            content = await file.read()
            validate_file_size(len(content))
            logger.info(
                f"[{request_id}] File size: {len(content)/1024:.2f} KB")
            raw_text = extract_text_from_image(content, preprocess=preprocess)

        elif file_type == "pdf":
            logger.info(
                f"[{request_id}] Received PDF OCR request: {file.filename}")
            # Validate file extension
            validate_file_extension(file.filename, {ALLOWED_PDF_EXTENSION})
            raw_text = extract_text_from_pdf(file_path, preprocess=preprocess)

        # Parse invoice
        logger.info(f"[{request_id}] Parsing invoice data")
        supplier = detect_supplier(raw_text)
        if supplier == 'UNKNOWN':
            raise HTTPException(
                status_code=500, detail="Unable to detect Supplier name , Please upload a correct bill or change the file ")
        parsed_data = parse_invoice_text(raw_text)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"[{request_id}] Processing completed in {processing_time:.2f}ms")

        return OCRResponse(
            success=True,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            raw_text=raw_text,
            parsed_data=to_parsed_invoice_model(parsed_data),
            processing_time_ms=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[{request_id}] Error processing image: {e}", exc_info=True)
        return OCRResponse(
            success=False,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )
    finally:
        # Cleanup temporary file
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.debug(f"[{request_id}] Temporary file cleaned up")
            except Exception as e:
                logger.warning(
                    f"[{request_id}] Failed to cleanup temp file: {e}")


# OCR text


@router.post("/text", response_model=OCRResponse)
async def parse_text(request: ParseTextRequest = Body(...)):
    """
    Parse already extracted text (no OCR needed)
    Useful when you already have the text and just need parsing

    Args:
        request: ParseTextRequest with raw text

    Returns:
        OCRResponse with parsed invoice data
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()

    logger.info(
        f"[{request_id}] Received text parsing request ({len(request.text)} characters)")

    try:
        # Parse invoice
        logger.info(f"[{request_id}] Parsing invoice data")
        parsed_data = parse_invoice_text(request.text)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"[{request_id}] Parsing completed in {processing_time:.2f}ms")

        return OCRResponse(
            success=True,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            raw_text=request.text,
            parsed_data=to_parsed_invoice_model(parsed_data),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error parsing text: {e}", exc_info=True)
        return OCRResponse(
            success=False,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )
