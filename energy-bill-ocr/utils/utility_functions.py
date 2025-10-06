
from fastapi import HTTPException
from PIL import Image, ImageEnhance
import os
import logging
from .Tesseract_config import MAX_FILE_SIZE

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
