
from fastapi import APIRouter, Body
from models import OCRResponse
from datetime import datetime
import uuid
from utils.utility_functions import logger
from services.parser import parse_energy_invoice
from models import ParsedInvoiceData, ParseTextRequest

route = APIRouter(prefix="/ocr")


@route.post("/parse-text", response_model=OCRResponse)
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
        parsed_data = parse_energy_invoice(request.text)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"[{request_id}] Parsing completed in {processing_time:.2f}ms")

        return OCRResponse(
            success=True,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            raw_text=request.text,
            parsed_data=ParsedInvoiceData(**parsed_data),
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
