from fastapi import APIRouter,  UploadFile, File, HTTPException, Depends
from schemas import OCRResponse
from datetime import datetime
import uuid
from utils.Tesseract_config import ALLOWED_IMAGE_EXTENSIONS
from utils.utility_functions import validate_file_extension, validate_file_size, logger, to_parsed_invoice_model
from services.ocr import extract_text_from_image
from services.parser_patterns import parse_invoice_text


route = APIRouter(prefix="/ocr", tags=["OCR"])


@route.post("/image", response_model=OCRResponse,)
async def ocr_image(
    file: UploadFile = File(...,
                            description="Image file to process"),
    preprocess: bool = True
):
    """
    Extract text from image and parse energy bill data

    Args:
        file: Image file upload (JPG, PNG, BMP, TIFF)
        preprocess: Whether to preprocess image (default: True)

    Returns:
        OCRResponse with parsed invoice data
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()

    logger.info(f"[{request_id}] Received image OCR request: {file.filename}")

    # Validate file extension
    validate_file_extension(file.filename, ALLOWED_IMAGE_EXTENSIONS)

    try:
        # Read file and validate size
        content = await file.read()
        validate_file_size(len(content))

        logger.info(f"[{request_id}] File size: {len(content)/1024:.2f} KB")

        # Extract text
        logger.info(f"[{request_id}] Starting OCR processing")
        raw_text = extract_text_from_image(content, preprocess=preprocess)

        # Parse invoice
        logger.info(f"[{request_id}] Parsing invoice data")
        parsed_data = parse_invoice_text(raw_text)
        print(parsed_data)

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
