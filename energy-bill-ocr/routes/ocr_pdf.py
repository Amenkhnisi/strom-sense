from fastapi import APIRouter,  UploadFile, File, HTTPException
from models import OCRResponse
import os
import tempfile
import logging
from datetime import datetime
import uuid
from utils.Tesseract_config import ALLOWED_PDF_EXTENSION
from utils.utility_functions import validate_file_extension, validate_file_size
from services.ocr import extract_text_from_pdf
from services.parser import parse_energy_invoice
from models import ParsedInvoiceData

route = APIRouter(prefix="/ocr")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@route.post("/pdf", response_model=OCRResponse)
async def ocr_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    preprocess: bool = True
):
    """
    Extract text from PDF and parse energy bill data

    Args:
        file: PDF file upload
        preprocess: Whether to preprocess images (default: True)

    Returns:
        OCRResponse with parsed invoice data
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()

    logger.info(f"[{request_id}] Received PDF OCR request: {file.filename}")

    # Validate file extension
    validate_file_extension(file.filename, {ALLOWED_PDF_EXTENSION})

    tmp_file_path = None

    try:
        # Read file and validate size
        content = await file.read()
        validate_file_size(len(content))

        logger.info(f"[{request_id}] File size: {len(content)/1024:.2f} KB")

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Extract text
        logger.info(f"[{request_id}] Starting OCR processing")
        raw_text = extract_text_from_pdf(tmp_file_path, preprocess=preprocess)

        # Parse invoice
        logger.info(f"[{request_id}] Parsing invoice data")
        parsed_data = parse_energy_invoice(raw_text)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"[{request_id}] Processing completed in {processing_time:.2f}ms")

        return OCRResponse(
            success=True,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            raw_text=raw_text,
            parsed_data=ParsedInvoiceData(**parsed_data),
            processing_time_ms=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[{request_id}] Error processing PDF: {e}", exc_info=True)
        return OCRResponse(
            success=False,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )
    finally:
        # Cleanup temporary file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
                logger.debug(f"[{request_id}] Temporary file cleaned up")
            except Exception as e:
                logger.warning(
                    f"[{request_id}] Failed to cleanup temp file: {e}")
