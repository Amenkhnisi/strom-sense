
from fastapi import APIRouter, Body
from schemas import OCRResponse
from datetime import datetime
import uuid
from utils.utility_functions import logger, to_parsed_invoice_model
from services.parser_patterns import parse_invoice_text
from schemas import ParseTextRequest

route = APIRouter(prefix="/ocr", tags=["OCR"])


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
