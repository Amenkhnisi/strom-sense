
from fastapi import HTTPException
from PIL import Image, ImageEnhance
import os
import logging
from .Tesseract_config import MAX_FILE_SIZE
from schemas import ParsedInvoiceData, FieldValue, BillingPeriod
from datetime import datetime
from typing import Union


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_file_size(file_size: int) -> None:
    """Validate uploaded file size"""
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB"
        )


def validate_file_extension(filename: str, allowed_extensions: set) -> None:
    """Validate file extension"""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy
    - Increase contrast
    - Sharpen
    - Convert to grayscale
    """
    try:
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Sharpen
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        return image
    except Exception as e:
        logger.warning(
            f"Image preprocessing failed: {e}. Using original image.")
        return image


def to_parsed_invoice_model(parsed_dict: dict) -> ParsedInvoiceData:
    supplier = parsed_dict.get("supplier", "UNKNOWN")

    # If already flat → return directly
    if "fields" not in parsed_dict:
        return ParsedInvoiceData(**parsed_dict)

    field_values = {
        key: val for key, val in parsed_dict["fields"].items()
        if isinstance(val, dict)
    }

    return ParsedInvoiceData(supplier=supplier, **field_values)


def normalize_field(field: Union[FieldValue, None], expected_type: str):
    if not field or not field.normalized:
        return None

    value = field.normalized

    if expected_type == "date":
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d.%m.%Y").date()
            except ValueError:
                return None
        return value

    if expected_type == "float":
        if isinstance(value, str):
            try:
                return float(value.replace(",", ".").replace("€", "").strip())
            except ValueError:
                return None
        return value

    if expected_type == "billing_period":
        if isinstance(value, dict):
            start = normalize_field(FieldValue(
                normalized=value.get("start_date")), "date")
            end = normalize_field(FieldValue(
                normalized=value.get("end_date")), "date")
            return start, end
        return None, None

    return value
